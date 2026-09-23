<template>
  <section class="page learn-page">
    <div class="learn-main">
      <el-alert
        v-if="!isEnrolled"
        class="trial-banner"
        type="warning"
        :closable="false"
        show-icon
        title="试看模式：仅可观看免费课时，开通课程后解锁全部内容"
      />
      <LessonPlayer
        :lesson="selectedLesson"
        :enrolled="isEnrolled"
        :course-id="courseId"
        @complete="complete"
      />
    </div>
    <aside class="learn-side">
      <ProgressIndicator v-if="isEnrolled" :percentage="progress?.progress || 0" type="circle" label="学习进度" />
      <el-alert v-else type="info" :closable="false" title="开通后记录学习进度" />
      <ChapterTree
        :chapters="chapters"
        :enrolled="isEnrolled"
        @select-lesson="selectLesson"
        @locked-lesson="lockedTip"
      />
      <el-input v-model="note" type="textarea" :rows="6" placeholder="学习笔记" />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import type { Lesson } from '@/types/lesson'

const route = useRoute()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const courseId = Number(route.params.courseId)
const selectedLesson = ref<Lesson | null>(null)
const note = ref('')
const chapters = computed(() => courseStore.chapters)
const course = computed(() => courseStore.currentCourse)
const progress = computed(() => enrollmentStore.progress)
const isEnrolled = computed(() => Boolean(course.value?.enrolled))

function firstAccessibleLesson(): Lesson | null {
  const all = chapters.value.flatMap((chapter) => chapter.lessons)
  return all.find((item) => !item.locked) || all[0] || null
}

function selectLesson(lesson: Lesson) {
  if (lesson.locked) {
    lockedTip()
    return
  }
  selectedLesson.value = lesson
}

function lockedTip() {
  ElMessage.warning('该课时已锁定，开通课程后即可学习')
}

async function complete(score?: number) {
  if (!isEnrolled.value || !selectedLesson.value) return
  await enrollmentStore.completeLesson(selectedLesson.value.id, score)
}

onMounted(async () => {
  await courseStore.fetchCourse(courseId)
  // 直接进入学习页的免费课程：补建学习关系（幂等）
  if (!course.value?.enrolled && Number(course.value?.price ?? 0) === 0) {
    await enrollmentStore.enrollFree(courseId)
    await courseStore.fetchCourse(courseId)
  }
  if (isEnrolled.value) await enrollmentStore.fetchProgress(courseId)

  const queryLessonId = Number(route.query.lesson)
  const queryLesson = chapters.value
    .flatMap((chapter) => chapter.lessons)
    .find((lesson) => lesson.id === queryLessonId && !lesson.locked)
  selectedLesson.value = queryLesson || firstAccessibleLesson()
})
</script>

<style scoped>
.learn-page {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
}

.learn-main {
  display: grid;
  gap: 12px;
}

.trial-banner {
  border-radius: 8px;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
}
</style>
