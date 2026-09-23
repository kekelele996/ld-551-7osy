import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Enrollment, ProgressSummary } from '@/types/enrollment'
import request from '@/utils/request'

export const useEnrollmentStore = defineStore('enrollment', () => {
  const enrollments = ref<Enrollment[]>([])
  const progress = ref<ProgressSummary | null>(null)

  async function fetchEnrollments() {
    enrollments.value = await request.get<unknown, Enrollment[]>('/enrollments')
  }

  /** 免费课程在详情页直接建立学习关系；已开通时幂等返回 */
  async function enrollFree(courseId: number) {
    const enrollment = await request.post<unknown, Enrollment>(`/enrollments/courses/${courseId}`)
    return enrollment
  }

  /** 未开通学员（试看）没有进度数据，404 时静默处理 */
  async function fetchProgress(courseId: number) {
    try {
      progress.value = await request.get<unknown, ProgressSummary>(`/enrollments/${courseId}/progress`)
    } catch (error) {
      if ((error as { response?: { status?: number } }).response?.status === 404) {
        progress.value = null
        return null
      }
      throw error
    }
    return progress.value
  }

  async function completeLesson(lessonId: number, score?: number) {
    const enrollment = await request.post<unknown, Enrollment>('/enrollments/progress/complete', { lesson_id: lessonId, score })
    await fetchProgress(enrollment.course_id)
    return enrollment
  }

  return { enrollments, progress, fetchEnrollments, enrollFree, fetchProgress, completeLesson }
})
