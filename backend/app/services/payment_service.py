from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants.enums import CourseStatus, OrderStatus
from app.exceptions.course import CourseNotFoundException
from app.exceptions.payment import InvalidOrderTransitionException, PaymentFailedException
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.order import Order
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.enrollment_service import EnrollmentService


class PaymentService:
    @staticmethod
    def create_order(db: Session, user: User, course_id: int, payment_method: str = "mock", ip_address: str | None = None) -> Order:
        course = db.get(Course, course_id)
        if not course or course.status != CourseStatus.PUBLISHED:
            raise CourseNotFoundException("课程不存在或未上架")
        if db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first():
            raise PaymentFailedException("已开通该课程，无需重复购买")
        if course.price <= 0:
            raise PaymentFailedException("免费课程可直接开通，无需下单支付")
        order = Order(
            order_no=f"EF{datetime.now(UTC):%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}",
            user_id=user.id,
            course_id=course_id,
            amount=course.price,
            payment_method=payment_method,
            status=OrderStatus.PENDING,
        )
        db.add(order)
        db.flush()
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Order", entity_id=str(order.id), after_data={"course_id": course_id, "amount": str(course.price)}, ip_address=ip_address)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def process_payment(db: Session, user: User, order_id: int, payment_info: dict, ip_address: str | None = None) -> Order:
        order = db.get(Order, order_id)
        if not order or order.user_id != user.id:
            raise PaymentFailedException("订单不存在")
        if order.status == OrderStatus.PAID:
            return order
        if order.status != OrderStatus.PENDING:
            raise InvalidOrderTransitionException()
        if order.created_at and order.created_at.replace(tzinfo=UTC) < datetime.now(UTC) - timedelta(minutes=30):
            order.status = OrderStatus.CANCELLED
            db.commit()
            raise InvalidOrderTransitionException("订单已超时取消")
        # 并发重复回调时开通关系的唯一约束可能先命中：回滚后按幂等订单重读重试
        try:
            return PaymentService._mark_paid_and_enroll(db, user, order, payment_info, ip_address)
        except IntegrityError:
            db.rollback()
            order = db.get(Order, order_id)
            if order and order.status == OrderStatus.PAID:
                return order
            raise

    @staticmethod
    def _mark_paid_and_enroll(db: Session, user: User, order: Order, payment_info: dict, ip_address: str | None) -> Order:
        order.status = OrderStatus.PAID
        order.payment_method = payment_info.get("payment_method", order.payment_method)
        order.paid_at = datetime.now(UTC)
        EnrollmentService.enroll(db, user, order.course, ip_address=ip_address)
        AuditService.record(db, user_id=user.id, action="UPDATE", entity="Order", entity_id=str(order.id), before_data={"status": OrderStatus.PENDING.value}, after_data={"status": OrderStatus.PAID.value}, ip_address=ip_address)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def refund(db: Session, user: User, order_id: int, ip_address: str | None = None) -> Order:
        order = db.get(Order, order_id)
        if not order or order.user_id != user.id:
            raise PaymentFailedException("订单不存在")
        if order.status != OrderStatus.PAID:
            raise InvalidOrderTransitionException()
        enrollment = db.query(Enrollment).filter_by(user_id=order.user_id, course_id=order.course_id).first()
        if enrollment:
            db.delete(enrollment)
            order.course.student_count = max(order.course.student_count - 1, 0)
        order.status = OrderStatus.REFUNDED
        AuditService.record(db, user_id=user.id, action="UPDATE", entity="Order", entity_id=str(order.id), before_data={"status": OrderStatus.PAID.value}, after_data={"status": OrderStatus.REFUNDED.value}, ip_address=ip_address)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def cancel(db: Session, user: User, order_id: int, ip_address: str | None = None) -> Order:
        order = db.get(Order, order_id)
        if not order or order.user_id != user.id:
            raise PaymentFailedException("订单不存在")
        if order.status != OrderStatus.PENDING:
            raise InvalidOrderTransitionException()
        order.status = OrderStatus.CANCELLED
        AuditService.record(db, user_id=user.id, action="UPDATE", entity="Order", entity_id=str(order.id), before_data={"status": OrderStatus.PENDING.value}, after_data={"status": OrderStatus.CANCELLED.value}, ip_address=ip_address)
        db.commit()
        db.refresh(order)
        return order
