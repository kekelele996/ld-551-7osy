<template>
  <section class="lesson-player">
    <el-empty v-if="lesson?.locked" :description="lockedText">
      <template #image>
        <el-icon class="locked-icon"><Lock /></el-icon>
      </template>
      <el-button type="primary" @click="emit('go-purchase')">前往开通</el-button>
    </el-empty>
    <template v-else-if="lesson">
      <header>
        <h2>{{ lesson.title }}</h2>
        <div class="badges">
          <el-tag v-if="lesson.is_free && !enrolled" size="small" type="success">试看</el-tag>
          <el-tag>{{ lesson.type }}</el-tag>
        </div>
      </header>
      <el-alert
        v-if="lesson.is_free && !enrolled"
        type="info"
        :closable="false"
        title="当前为免费试看课时，开通课程后可学习全部课时并记录进度"
        class="preview-tip"
      />
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
    </template>
    <el-empty v-else description="请选择课时" />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import { LessonType } from '@/constants/enums'
import type { Lesson } from '@/types/lesson'

const props = withDefaults(defineProps<{ lesson: Lesson | null; enrolled?: boolean }>(), { enrolled: true })
const emit = defineEmits<{ complete: [score?: number]; 'go-purchase': [] }>()
const answer = ref('')

const lockedText = '该课时已锁定，开通课程后即可学习'

function complete() {
  // 未开通只能试看，不产生学习进度
  if (!props.enrolled) return
  emit('complete')
}

function submitQuiz() {
  if (!props.enrolled) return
  emit('complete', answer.value.trim() ? 100 : 0)
}

function handleScroll(event: Event) {
  if (!props.enrolled) return
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

.badges {
  display: flex;
  gap: 6px;
}

.preview-tip {
  margin: 12px 0;
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

.locked-icon {
  font-size: 48px;
  color: #9ca3af;
}
</style>
