from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.constants.enums import CourseStatus, UserRole
from app.exceptions.course import CourseNotFoundException
from app.exceptions.payment import PaymentFailedException
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import LessonProgress
from app.models.user import User
from app.services.audit_service import AuditService


class EnrollmentService:
    @staticmethod
    def is_enrolled(db: Session, user_id: int, course_id: int) -> bool:
        return db.query(Enrollment.id).filter_by(user_id=user_id, course_id=course_id).first() is not None

    @staticmethod
    def can_access_full_content(db: Session, user: User | None, course: Course) -> bool:
        """已开通学员、课程讲师、管理员可看全部课时正文（课程下架后也不例外）。"""
        if user is None:
            return False
        if user.role == UserRole.ADMIN or course.instructor_id == user.id:
            return True
        return EnrollmentService.is_enrolled(db, user.id, course.id)

    @staticmethod
    def enroll(db: Session, user: User, course: Course, ip_address: str | None = None) -> Enrollment:
        existing = db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).first()
        if existing:
            return existing
        enrollment = Enrollment(user_id=user.id, course_id=course.id)
        try:
            # 用保存点包住插入：并发下唯一约束冲突时只回滚插入，不影响外层事务（如支付状态更新）
            with db.begin_nested():
                db.add(enrollment)
                db.flush()
        except IntegrityError:
            # 重复开通直接复用已有学习关系，学员数保持不变
            return db.query(Enrollment).filter_by(user_id=user.id, course_id=course.id).one()
        # 插入成功（保存点已释放）后再累加学员数，随外层事务一起提交
        course.student_count += 1
        AuditService.record(db, user_id=user.id, action="CREATE", entity="Enrollment", entity_id=str(enrollment.id), after_data={"course_id": course.id}, ip_address=ip_address)
        return enrollment

    @staticmethod
    def enroll_free_course(db: Session, user: User, course_id: int, ip_address: str | None = None) -> Enrollment:
        """免费课程在详情页直接开通；已开通时幂等返回。"""
        course = db.get(Course, course_id)
        if not course or course.status != CourseStatus.PUBLISHED:
            raise CourseNotFoundException("课程不存在或未上架")
        existing = db.query(Enrollment).filter_by(user_id=user.id, course_id=course_id).first()
        if existing:
            return existing
        if course.price != 0:
            raise PaymentFailedException("付费课程需完成支付后开通")
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
            raise CourseNotFoundException("尚未注册该课程")
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
            raise CourseNotFoundException("尚未注册该课程")
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == course_id).count()
        completed = db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).count()
        return enrollment, completed, total

    @staticmethod
    def recalculate_progress(db: Session, enrollment: Enrollment) -> None:
        total = db.query(Lesson).join(Chapter).filter(Chapter.course_id == enrollment.course_id).count()
        completed = db.query(LessonProgress).filter_by(enrollment_id=enrollment.id).count()
        enrollment.progress = round((completed / total) * 100, 2) if total else 0
