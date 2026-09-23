import type { LessonType } from '@/constants/enums'

export interface Lesson {
  id: number
  chapter_id: number
  title: string
  type: LessonType
  content: string
  duration: number
  is_free: boolean
  locked: boolean
  sort_order: number
}
