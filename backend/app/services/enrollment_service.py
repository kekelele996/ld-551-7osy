from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.constants.enums import CourseStatus
from app.exceptions.course import CourseNotFoundException
from app.exceptions.payment import PaymentFailedException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.user import User
from app.services.access_service import AccessService
from app.services.audit_service import AuditService


class EnrollmentService:
    @staticmethod
    def enroll(db: Session, user: User, course: Course, ip_address: str | None = None) -> Enrollment:
        """建立学习关系。已存在时直接返回，不重复增加学员数。"""
        existing = db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).first()
        if existing:
            return existing
        enrollment = Enrollment(user_id=user.id, course_id=course.id)
        db.add(enrollment)
        course.student_count += 1
        try:
            db.flush()
        except IntegrityError:
            # 并发场景下唯一约束兜底：不重复开通、不重复增加学员数
            db.rollback()
            return db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).one()
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Enrollment", entity_id=str(enrollment.id), after_data={"course_id": course.id}, ip_address=ip_address)
        return enrollment

    @staticmethod
    def enroll_free_course(db: Session, user: User, course_id: int, ip_address: str | None = None) -> Enrollment:
        """免费课程在详情页直接开通；付费课程必须走支付流程。"""
        course = db.get(Course, course_id)
        if not course or course.status != CourseStatus.PUBLISHED:
            raise CourseNotFoundException("课程不存在或未上架")
        if course.price > 0:
            raise PaymentFailedException("付费课程请完成支付后开通")
        enrollment = EnrollmentService.enroll(db, user, course, ip_address=ip_address)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def list_user_enrollments(db: Session, user: User) -> list[Enrollment]:
        return (
            db.query(Enrollment)
            .options(joinedload(Enrollment.course).joinedload(Course.instructor))
            .filter(Enrollment.user_id == user.id)
            .order_by(Enrollment.last_access_at.desc())
            .all()
        )

    @staticmethod
    def complete_lesson(db: Session, user: User, lesson_id: int, score: int | None = None, ip_address: str | None = None) -> Enrollment:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        course_id = lesson.chapter.course_id
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            # 未开通学员即使是试看课时也只能预览，不能记录学习进度
            if AccessService.can_access_lesson(db, user, lesson):
                raise CourseNotFoundException("试看课时不记录进度，请先开通课程")
            raise CourseNotFoundException("尚未开通该课程")
        progress = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id, lesson_id=lesson_id).first()
        if not progress:
            progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id, score=score)
            db.add(progress)
            db.flush()
            AuditService.record(db, user_id=user.id, action="CREATE", entity="LessonProgress", entity_id=str(progress.id), after_data={"lesson_id": lesson_id, "score": score}, ip_address=ip_address)
        elif score is not None:
            progress.score = score
        enrollment.last_access_at = datetime.now(UTC)
        EnrollmentService.recalculate_progress(db, enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_progress(db: Session, user: User, course_id: int) -> tuple[Enrollment, int, int]:
        enrollment = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if not enrollment:
            raise CourseNotFoundException("尚未开通该课程")
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == course_id).count()
        completed = db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).count()
        return enrollment, completed, total

    @staticmethod
    def recalculate_progress(db: Session, enrollment: Enrollment) -> None:
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == enrollment.course_id).count()
        completed = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id).count()
        enrollment.progress = round((completed / total) * 100, 2) if total else 0
