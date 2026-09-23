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
          <el-button v-if="course.enrolled" type="primary" @click="$router.push(`/learn/${course.id}`)">继续学习</el-button>
          <el-button v-else-if="Number(course.price) === 0" type="primary" :loading="enrolling" @click="enrollFree">
            免费注册
          </el-button>
          <el-button v-else type="primary" :loading="orderStore.currentOrder?.status === 'PENDING'" @click="buy">
            立即购买
          </el-button>
        </div>
      </div>
    </div>
    <el-tabs>
      <el-tab-pane label="大纲">
        <ChapterTree :chapters="chapters" />
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
import { formatMinutes, formatMoney } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const enrollmentStore = useEnrollmentStore()
const orderStore = useOrderStore()
const course = computed(() => courseStore.currentCourse)
const chapters = computed(() => courseStore.chapters)
const enrolling = ref(false)

async function refreshCourse() {
  await courseStore.fetchCourse(Number(route.params.id))
}

async function enrollFree() {
  if (!course.value) return
  enrolling.value = true
  try {
    await enrollmentStore.enrollFree(course.value.id)
    ElMessage.success('注册成功，开始学习吧')
    await refreshCourse()
    router.push(`/learn/${course.value.id}`)
  } finally {
    enrolling.value = false
  }
}

async function buy() {
  if (!course.value) return
  // 付费课程：下单并支付成功后才开通
  const order = await orderStore.createOrder(course.value.id)
  const paid = await orderStore.payOrder(order.id)
  if (paid.status === 'PAID') {
    ElMessage.success('支付成功，已开通课程')
    await refreshCourse()
    router.push(`/learn/${course.value.id}`)
  }
}

onMounted(refreshCourse)
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
