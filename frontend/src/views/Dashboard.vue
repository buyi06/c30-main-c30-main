<template>
  <div class="dashboard">
    <!-- 头部状态栏 -->
    <div class="header">
      <div class="status-bar">
        <status-indicator :status="serviceStatus" />
        <van-tag :type="periodTagType" size="medium">{{ periodLabel }}</van-tag>
      </div>
      <van-icon name="setting-o" size="24" class="settings-btn" @click="$router.push('/settings')" />
    </div>

    <!-- 课程列表 -->
    <van-pull-refresh v-model="loading" @refresh="onRefresh">
      <div class="content">
        <div v-if="courses.length === 0" class="empty-tip">
          <van-empty description="今日无课程" />
        </div>

        <course-card
          v-for="course in courses"
          :key="course.id || course.faceTeachId"
          :course="course"
          @click="goCourseDetail(course)"
        />
      </div>
    </van-pull-refresh>

    <!-- 快捷操作栏 -->
    <div class="action-bar">
      <van-button type="primary" size="small" @click="doRefresh" :loading="refreshing">
        立即刷新
      </van-button>
      <van-button
        :type="paused ? 'success' : 'default'"
        size="small"
        @click="togglePause"
      >
        {{ paused ? '恢复自动' : '暂停自动' }}
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStatus, getCoursesToday, manualRefresh, schedulerPause, schedulerResume } from '../api/index.js'
import StatusIndicator from '../components/StatusIndicator.vue'
import CourseCard from '../components/CourseCard.vue'

const router = useRouter()
const loading = ref(false)
const refreshing = ref(false)
const paused = ref(false)
const statusData = ref({})
const courses = ref([])

// 计算属性
const serviceStatus = computed(() => statusData.value.service?.status || 'running')
const periodLabel = computed(() => {
  const period = statusData.value.service?.current_period || 'no_class_today'
  const map = {
    pre_class: '课前',
    in_class: '课中',
    between: '课间',
    weekend: '周末',
    no_class_today: '无课',
  }
  return map[period] || period
})

const periodTagType = computed(() => {
  const period = statusData.value.service?.current_period || 'no_class_today'
  const map = {
    pre_class: 'primary',
    in_class: 'success',
    between: 'warning',
    weekend: 'default',
    no_class_today: 'default',
  }
  return map[period] || 'default'
})

// 刷新数据
const fetchStatus = async () => {
  try {
    const res = await getStatus()
    if (res.data.code === 200) {
      statusData.value = res.data.result
    }
  } catch (e) { /* ignore */ }
}

const fetchCourses = async () => {
  try {
    const res = await getCoursesToday()
    if (res.data.code === 200) {
      courses.value = res.data.result || []
    }
  } catch (e) { /* ignore */ }
}

const onRefresh = async () => {
  await Promise.all([fetchStatus(), fetchCourses()])
  loading.value = false
}

const doRefresh = async () => {
  refreshing.value = true
  try {
    await manualRefresh()
    await onRefresh()
  } finally {
    refreshing.value = false
  }
}

const togglePause = async () => {
  try {
    if (paused.value) {
      await schedulerResume()
      paused.value = false
      showToast('已恢复')
    } else {
      await schedulerPause()
      paused.value = true
      showToast('已暂停')
    }
  } catch (e) {
    showToast('操作失败')
  }
}

const goCourseDetail = (course) => {
  router.push(`/course/${course.id || course.faceTeachId}`)
}

const showToast = (msg) => {
  import('vant').then(({ showToast }) => {
    showToast({ message: msg, duration: 2000 })
  })
}

// 定时刷新状态
let timer = null
onMounted(() => {
  fetchStatus()
  fetchCourses()
  timer = setInterval(fetchStatus, 10000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.dashboard {
  padding-bottom: 60px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-btn {
  cursor: pointer;
}

.content {
  padding: 16px;
}

.empty-tip {
  padding: 40px 0;
}

.action-bar {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  background: #fff;
}
</style>