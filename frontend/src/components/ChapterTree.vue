<template>
  <el-tree
    class="chapter-tree"
    :data="treeData"
    node-key="key"
    default-expand-all
    :draggable="false"
    @node-click="handleClick"
  >
    <template #default="{ data }">
      <span class="tree-node" :class="{ 'is-locked': data.lesson?.locked }">
        <span>{{ data.label }}</span>
        <span class="tags">
          <el-tag v-if="data.lesson?.is_free && !enrolled" size="small" type="success">试看</el-tag>
          <el-tag v-if="data.lesson?.locked" size="small" type="info">
            <el-icon class="lock-icon"><Lock /></el-icon>锁定
          </el-tag>
        </span>
      </span>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import type { Chapter } from '@/types/chapter'
import type { Lesson } from '@/types/lesson'

const props = withDefaults(defineProps<{ chapters: Chapter[]; enrolled?: boolean }>(), { enrolled: false })
const emit = defineEmits<{ selectLesson: [lesson: Lesson]; lockedLesson: [] }>()

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
  if (!data.lesson) return
  if (data.lesson.locked) {
    emit('lockedLesson')
    return
  }
  emit('selectLesson', data.lesson)
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
  gap: 8px;
}

.tags {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

.is-locked {
  color: #9ca3af;
}

.lock-icon {
  vertical-align: middle;
}
</style>
