<template>
  <section class="page learn-page">
    <div class="learn-main">
      <LessonPlayer
        :lesson="activeLesson"
        :enrolled="enrolled"
        @complete="complete"
        @go-purchase="router.push(`/courses/${courseId}`)"
      />
    </div>
    <aside class="learn-side">
      <template v-if="enrolled">
        <ProgressIndicator :percentage="progress?.progress || 0" type="circle" label="学习进度" />
      </template>
      <el-alert
        v-else
        type="warning"
        :closable="false"
        show-icon
        title="尚未开通该课程"
        description="仅可观看免费试看课时，开通后解锁全部课时。"
      >
        <el-button size="small" type="primary" @click="router.push(`/courses/${courseId}`)">前往开通</el-button>
      </el-alert>
      <ChapterTree :chapters="chapters" @select-lesson="openLesson" />
      <el-input v-if="enrolled" v-model="note" type="textarea" :rows="6" placeholder="学习笔记" />
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import LessonPlayer from '@/components/LessonPlayer.vue'
import ProgressIndicator from '@/components/ProgressIndicator.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import request from '@/utils/request'
import type { Lesson } from '@/types/lesson'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const courseId = Number(route.params.courseId)
const note = ref('')
const activeLesson = ref<Lesson | null>(null)
const chapters = computed(() => courseStore.chapters)
const progress = computed(() => enrollmentStore.progress)
const enrolled = computed(() => Boolean(courseStore.currentCourse?.enrolled))

const firstPlayableLesson = computed<Lesson | null>(() => {
  for (const chapter of chapters.value) {
    const lesson = chapter.lessons.find((item) => enrolled.value || item.is_free)
    if (lesson) return lesson
  }
  return null
})

async function openLesson(lesson: Lesson) {
  // 未开通只能打开试看课时；锁定课时由章节树拦截，这里再兜一层
  if (!enrolled.value && lesson.locked) {
    ElMessage.warning('该课时已锁定，开通课程后即可学习')
    return
  }
  // 以服务端为准拉取课时，避免使用列表上残留的正文/锁定状态
  activeLesson.value = await request.get<unknown, Lesson>(`/lessons/${lesson.id}`)
}

async function complete(score?: number) {
  if (!enrolled.value || !activeLesson.value) return
  await enrollmentStore.completeLesson(activeLesson.value.id, score)
}

onMounted(async () => {
  await courseStore.fetchCourse(courseId)
  if (enrolled.value) {
    await enrollmentStore.fetchProgress(courseId)
  }
  const first = firstPlayableLesson.value
  if (first) await openLesson(first)
})
</script>

<style scoped>
.learn-page {
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 3fr);
  gap: 20px;
}

.learn-main {
  min-width: 0;
}

.learn-side {
  display: grid;
  gap: 16px;
  align-content: start;
}
</style>
