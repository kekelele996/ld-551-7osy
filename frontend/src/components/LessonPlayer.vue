<template>
  <section class="lesson-player">
    <template v-if="lesson && !lesson.locked">
      <header>
        <h2>{{ lesson.title }}</h2>
        <div class="header-tags">
          <el-tag v-if="lesson.is_free" type="success" size="small">试看</el-tag>
          <el-tag>{{ lesson.type }}</el-tag>
        </div>
      </header>
      <video v-if="lesson.type === LessonType.VIDEO" controls class="video" @ended="complete">
        <source :src="lesson.content" />
      </video>
      <article v-else-if="lesson.type === LessonType.TEXT" class="text-content" @scroll.passive="handleScroll">
        {{ lesson.content }}
      </article>
      <el-form v-else class="quiz" @submit.prevent>
        <el-form-item label="答案">
          <el-input v-model="answer" placeholder="请输入测验答案" />
        </el-form-item>
        <el-button type="primary" @click="submitQuiz">提交测验</el-button>
      </el-form>
      <el-button v-if="enrolled" class="complete" type="success" plain @click="complete">标记完成</el-button>
      <p v-else class="trial-tip">当前为试看内容，<router-link :to="`/courses/${courseId}`">开通课程</router-link>后可记录学习进度</p>
    </template>
    <el-result
      v-else-if="lesson"
      icon="lock"
      title="该课时已锁定"
      sub-title="开通课程后即可学习全部课时"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push(`/courses/${courseId}`)">去开通</el-button>
      </template>
    </el-result>
    <el-empty v-else description="请选择课时" />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { LessonType } from '@/constants/enums'
import type { Lesson } from '@/types/lesson'

const props = defineProps<{ lesson: Lesson | null; enrolled?: boolean; courseId: number }>()
const emit = defineEmits<{ complete: [score?: number] }>()
const answer = ref('')

function complete() {
  // 未开通学员只能试看，不产生完成事件
  if (!props.enrolled) return
  emit('complete')
}

function submitQuiz() {
  if (!props.enrolled) return
  emit('complete', answer.value.trim() ? 100 : 0)
}

function handleScroll(event: Event) {
  const el = event.target as HTMLElement
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) complete()
}
</script>

<style scoped>
.lesson-player {
  min-height: 520px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.video {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #111827;
  border-radius: 8px;
}

.text-content {
  height: 360px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #374151;
}

.complete {
  margin-top: 16px;
}

.trial-tip {
  margin-top: 12px;
  color: #92400e;
  font-size: 13px;
}
</style>
