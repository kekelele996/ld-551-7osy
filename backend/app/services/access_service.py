from sqlalchemy.orm import Session

from app.constants.enums import CourseStatus, UserRole
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.chapter import ChapterResponse
from app.schemas.lesson import LessonResponse

LOCKED_LESSON_CONTENT = ""


class AccessService:
    """课程开通关系与课时访问规则。"""

    @staticmethod
    def is_enrolled(db: Session, user: User | None, course_id: int) -> bool:
        if not user:
            return False
        return (
            db.query(Enrollment.id)
            .filter(Enrollment.user_id == user.id, Enrollment.course_id == course_id)
            .first()
            is not None
        )

    @staticmethod
    def is_course_staff(user: User | None, course: Course) -> bool:
        """讲师可管理自己的课程，管理员拥有全部访问权。"""
        if not user:
            return False
        if user.role == UserRole.ADMIN:
            return True
        return user.role == UserRole.INSTRUCTOR and course.instructor_id == user.id

    @staticmethod
    def can_view_course(db: Session, user: User | None, course: Course) -> bool:
        if course.status == CourseStatus.PUBLISHED:
            return True
        return AccessService.is_course_staff(user, course) or AccessService.is_enrolled(db, user, course.id)

    @staticmethod
    def can_access_lesson(db: Session, user: User | None, lesson: Lesson) -> bool:
        course = lesson.chapter.course
        if AccessService.is_course_staff(user, course):
            return True
        if AccessService.is_enrolled(db, user, course.id):
            return True
        # 未开通学员只能访问已上架课程中的免费试看课时
        return lesson.is_free and course.status == CourseStatus.PUBLISHED

    @staticmethod
    def serialize_lesson(lesson: Lesson, *, accessible: bool) -> LessonResponse:
        if accessible:
            return LessonResponse.model_validate(lesson)
        return LessonResponse(
            id=lesson.id,
            chapter_id=lesson.chapter_id,
            title=lesson.title,
            type=lesson.type,
            content=LOCKED_LESSON_CONTENT,
            duration=lesson.duration,
            is_free=lesson.is_free,
            sort_order=lesson.sort_order,
            locked=True,
        )

    @staticmethod
    def serialize_chapters(db: Session, user: User | None, course: Course) -> list[ChapterResponse]:
        staff = AccessService.is_course_staff(user, course)
        enrolled = AccessService.is_enrolled(db, user, course.id)
        public_course = course.status == CourseStatus.PUBLISHED
        result: list[ChapterResponse] = []
        for chapter in course.chapters:
            lessons = [
                AccessService.serialize_lesson(
                    lesson,
                    accessible=staff or enrolled or (lesson.is_free and public_course),
                )
                for lesson in chapter.lessons
            ]
            result.append(
                ChapterResponse(
                    id=chapter.id,
                    course_id=chapter.course_id,
                    title=chapter.title,
                    sort_order=chapter.sort_order,
                    lessons=lessons,
                )
            )
        return result
