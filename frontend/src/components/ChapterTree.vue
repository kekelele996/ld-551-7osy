<template>
  <el-tree
    class="chapter-tree"
    :data="treeData"
    node-key="key"
    default-expand-all
    :expand-on-click-node="false"
    @node-click="handleClick"
  >
    <template #default="{ data }">
      <span class="tree-node" :class="{ 'is-locked': data.lesson?.locked }">
        <span class="tree-label">
          <el-icon v-if="data.lesson?.locked" class="lock-icon" title="未开通，课时已锁定"><Lock /></el-icon>
          <span>{{ data.label }}</span>
        </span>
        <el-tag v-if="data.lesson?.is_free" size="small" type="success">试看</el-tag>
      </span>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import type { Chapter } from '@/types/chapter'
import type { Lesson } from '@/types/lesson'

const props = defineProps<{ chapters: Chapter[] }>()
const emit = defineEmits<{ selectLesson: [lesson: Lesson] }>()

const treeData = computed(() =>
  props.chapters.map((chapter) => ({
    key: `chapter-${chapter.id}`,
    label: `${chapter.sort_order}. ${chapter.title}`,
    children: chapter.lessons.map((lesson) => ({
      key: `lesson-${lesson.id}`,
      label: `${lesson.sort_order}. ${lesson.title} · ${lesson.duration}分钟`,
      lesson
    }))
  }))
)

function handleClick(data: { lesson?: Lesson }) {
  // 未开通的付费课时不允许打开
  if (data.lesson && !data.lesson.locked) emit('selectLesson', data.lesson)
}
</script>

<style scoped>
.chapter-tree {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
}

.tree-node {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.tree-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.is-locked {
  color: #9ca3af;
  cursor: not-allowed;
}

.lock-icon {
  color: #9ca3af;
}
</style>
