<template>
  <div class="dashboard">
    <!-- 渐变头部 -->
    <div class="header">
      <div class="header-bg"></div>
      <div class="header-content">
        <div class="header-top">
          <div class="greeting">
            <div class="greeting-title">C30 管理面板</div>
            <div class="greeting-sub">{{ periodEmoji }} {{ periodLabel }}</div>
          </div>
          <van-icon name="setting-o" size="22" class="settings-btn" @click="$router.push('/settings')" />
        </div>

        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-icon sign-icon">
              <van-icon name="success" size="18" />
            </div>
            <div class="stat-value">{{ activityStats.sign_done }}</div>
            <div class="stat-label">签到完成</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon discuss-icon">
              <van-icon name="chat-o" size="18" />
            </div>
            <div class="stat-value">{{ activityStats.discuss_done }}</div>
            <div class="stat-label">讨论完成</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon pending-icon">
              <van-icon name="clock-o" size="18" />
            </div>
            <div class="stat-value">{{ activityStats.pending }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态指示 -->
    <div class="status-strip">
      <status-indicator :status="serviceStatus" />
      <div class="status-actions">
        <van-button
          size="mini"
          round
          plain
          type="primary"
          :icon="paused ? 'play-circle-o' : 'pause-circle-o'"
          @click="togglePause"
        >
          {{ paused ? '恢复' : '暂停' }}
        </van-button>
        <van-button
          size="mini"
          round
          plain
          type="primary"
          icon="replay"
          @click="doRefresh"
          :loading="refreshing"
        >
          刷新
        </van-button>
      </div>
    </div>

    <!-- 课程列表 -->
    <van-pull-refresh v-model="loading" @refresh="onRefresh" success-text="已刷新">
      <div class="content">
        <div class="section-header">
          <span class="section-title">今日课程</span>
          <span class="section-count">{{ courses.length }} 门</span>
        </div>

        <div v-if="courses.length === 0" class="empty-state">
          <div class="empty-icon">🎉</div>
          <div class="empty-text">今日无课程</div>
          <div class="empty-sub">享受自由时间吧</div>
        </div>

        <course-card
          v-for="course in courses"
          :key="course.id || course.faceTeachId"
          :course="course"
          @click="goCourseDetail(course)"
        />
      </div>
    </van-pull-refresh>
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

const serviceStatus = computed(() => statusData.value.service?.status || 'running')

const periodLabel = computed(() => {
  const period = statusData.value.service?.current_period || 'no_class_today'
  const map = {
    pre_class: '课前准备',
    in_class: '课程进行中',
    between: '课间休息',
    weekend: '周末休假',
    no_class_today: '今日无课',
  }
  return map[period] || period
})

const periodEmoji = computed(() => {
  const period = statusData.value.service?.current_period || 'no_class_today'
  const map = {
    pre_class: '📖',
    in_class: '🎯',
    between: '☕',
    weekend: '🌴',
    no_class_today: '🌙',
  }
  return map[period] || '📚'
})

const activityStats = computed(() => {
  const acts = statusData.value.activities || {}
  const sign_done = (acts.sign_in?.done || 0) + (acts.sign_out?.done || 0)
  const discuss_done = acts.discuss?.done || 0
  const pending = (acts.sign_in?.pending || 0) + (acts.sign_out?.pending || 0) +
    (acts.discuss?.pending || 0) + (acts.brainstorm?.pending || 0) + (acts.vote?.pending || 0)
  return { sign_done, discuss_done, pending }
})

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
      showToast('已恢复自动调度')
    } else {
      await schedulerPause()
      paused.value = true
      showToast('已暂停自动调度')
    }
  } catch (e) {
    showToast('操作失败')
  }
}

const goCourseDetail = (course) => {
  router.push({ path: `/course/${course.id || course.faceTeachId}`, query: { name: course.courseName } })
}

const showToast = (msg) => {
  import('vant').then(({ showToast }) => {
    showToast({ message: msg, duration: 2000 })
  })
}

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
  padding-bottom: 80px;
}

/* 渐变头部 */
.header {
  position: relative;
  overflow: hidden;
  padding-bottom: 8px;
}

.header-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
  border-radius: 0 0 24px 24px;
}

.header-content {
  position: relative;
  padding: 20px 20px 16px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.greeting-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.greeting-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.8);
  margin-top: 2px;
}

.settings-btn {
  color: rgba(255,255,255,0.9) !important;
  background: rgba(255,255,255,0.15);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(4px);
}

/* 统计卡片行 */
.stats-row {
  display: flex;
  gap: 10px;
}

.stat-card {
  flex: 1;
  background: rgba(255,255,255,0.95);
  border-radius: var(--radius);
  padding: 14px 12px;
  text-align: center;
  backdrop-filter: blur(8px);
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
}

.sign-icon {
  background: var(--success-light);
  color: var(--success);
}

.discuss-icon {
  background: var(--info-light);
  color: var(--info);
}

.pending-icon {
  background: var(--warning-light);
  color: var(--warning);
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* 状态条 */
.status-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--card);
  margin: 12px 16px 0;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.status-actions {
  display: flex;
  gap: 8px;
}

/* 课程区 */
.content {
  padding: 0 16px 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 4px 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.section-count {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg);
  padding: 2px 10px;
  border-radius: 10px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 48px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
}

.empty-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>