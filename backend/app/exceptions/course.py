class CourseNotFoundException(Exception):
    def __init__(self, message: str = "课程不存在"):
        self.message = message
        super().__init__(message)


class CoursePermissionException(Exception):
    def __init__(self, message: str = "无权操作该课程"):
        self.message = message
        super().__init__(message)


class LessonLockedException(Exception):
    def __init__(self, message: str = "该课时已锁定，请先开通课程"):
        self.message = message
        super().__init__(message)
