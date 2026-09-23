<template>
  <section class="page" v-if="course">
    <div class="detail-head">
      <img :src="course.cover_image" :alt="course.title" />
      <div>
        <el-tag>{{ course.category }}</el-tag>
        <h1>{{ course.title }}</h1>
        <p>{{ course.description }}</p>
        <div class="detail-meta">
          <span>{{ course.instructor?.name }}</span>
          <span>{{ formatMinutes(course.total_duration) }}</span>
          <span>评分 {{ course.rating }}</span>
        </div>
        <strong class="price">{{ formatMoney(course.price) }}</strong>
        <div class="actions">
          <el-button v-if="isEnrolled" type="primary" @click="goLearn">继续学习</el-button>
          <template v-else>
            <el-button v-if="isFree" type="primary" :loading="enrolling" @click="enrollFree">免费注册</el-button>
            <el-button v-else type="primary" :loading="paying" @click="buy">立即购买</el-button>
          </template>
        </div>
      </div>
    </div>
    <el-tabs>
      <el-tab-pane label="大纲">
        <ChapterTree
          :chapters="chapters"
          :enrolled="isEnrolled"
          @select-lesson="previewLesson"
          @locked-lesson="lockedTip"
        />
      </el-tab-pane>
      <el-tab-pane label="介绍">
        <article class="rich-text">{{ course.description }}</article>
      </el-tab-pane>
      <el-tab-pane label="评价">
        <el-empty description="评价模块预留，评分已在课程卡片展示" />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChapterTree from '@/components/ChapterTree.vue'
import { useCourseStore } from '@/stores/courseStore'
import { useEnrollmentStore } from '@/stores/enrollmentStore'
import { useOrderStore } from '@/stores/orderStore'
import type { Lesson } from '@/types/lesson'
import { formatMinutes, formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const orderStore = useOrderStore()
const course = computed(() => courseStore.currentCourse)
const chapters = computed(() => courseStore.chapters)
const isEnrolled = computed(() => Boolean(course.value?.enrolled))
const isFree = computed(() => Number(course.value?.price ?? 0) === 0)
const enrolling = ref(false)
const paying = ref(false)

async function enrollFree() {
  if (!course.value) return
  enrolling.value = true
  try {
    await enrollmentStore.enrollFree(course.value.id)
    ElMessage.success('开通成功，开始学习吧')
    goLearn()
  } finally {
    enrolling.value = false
  }
}

async function buy() {
  if (!course.value) return
  paying.value = true
  try {
    const order = await orderStore.createOrder(course.value.id)
    await orderStore.payOrder(order.id)
    ElMessage.success('支付成功，已开通课程')
    goLearn()
  } finally {
    paying.value = false
  }
}

function goLearn() {
  if (course.value) router.push(`/learn/${course.value.id}`)
}

function previewLesson(lesson: Lesson) {
  if (!course.value) return
  router.push({ path: `/learn/${course.value.id}`, query: { lesson: String(lesson.id) } })
}

function lockedTip() {
  ElMessage.warning('该课时已锁定，开通课程后即可学习')
}

onMounted(() => courseStore.fetchCourse(Number(route.params.id)))
</script>

<style scoped>
.detail-head {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 28px;
  padding: 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 20px;
}

.detail-head img {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  border-radius: 8px;
}

.detail-meta,
.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.price {
  display: block;
  margin: 16px 0;
  font-size: 28px;
  color: #b45309;
}

.rich-text {
  line-height: 1.8;
  background: #fff;
  padding: 18px;
  border-radius: 8px;
}
</style>
