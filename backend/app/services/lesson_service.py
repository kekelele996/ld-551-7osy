from sqlalchemy.orm import Session

from app.constants.enums import CourseStatus
from app.exceptions.course import CourseNotFoundException
from app.models.chapter import Chapter
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.chapter import ChapterCreate
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService


class LessonService:
    @staticmethod
    def create_chapter(db: Session, payload: ChapterCreate) -> Chapter:
        chapter = Chapter(**payload.model_dump())
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    @staticmethod
    def create_lesson(db: Session, payload: LessonCreate) -> Lesson:
        chapter = db.get(Chapter, payload.chapter_id)
        if not chapter:
            raise CourseNotFoundException("章节不存在")
        lesson = Lesson(**payload.model_dump())
        db.add(lesson)
        db.flush()
        CourseService.recalculate_course_stats(db, chapter.course_id)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def get_lesson(db: Session, lesson_id: int, user: User | None = None) -> Lesson:
        """供接口使用：按访问者开通情况控制正文。知道课时地址也不能绕过开通规则。"""
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        chapter = db.get(Chapter, lesson.chapter_id)
        course = CourseService.get_course(db, chapter.course_id)
        has_full_access = EnrollmentService.can_access_full_content(db, user, course)
        if course.status != CourseStatus.PUBLISHED and not has_full_access:
            raise CourseNotFoundException()
        lesson.locked = not has_full_access and not lesson.is_free
        if lesson.locked:
            lesson.content = ""
        return lesson

    @staticmethod
    def update_lesson(db: Session, lesson_id: int, payload: LessonUpdate) -> Lesson:
        lesson = db.get(Lesson, lesson_id)
        if not lesson:
            raise CourseNotFoundException("课时不存在")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(lesson, key, value)
        db.flush()
        CourseService.recalculate_course_stats(db, lesson.chapter.course_id)
        db.commit()
        db.refresh(lesson)
        return lesson
