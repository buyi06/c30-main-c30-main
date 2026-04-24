<template>
  <div class="course-detail">
    <!-- 课程头部 -->
    <div class="course-header" :class="{ ended: course?.state === 3 }">
      <div class="course-header-bg"></div>
      <div class="course-header-content">
        <van-icon name="arrow-left" size="20" class="back-btn" @click="$router.back()" />
        <div class="course-title">{{ course?.courseName || '课程详情' }}</div>
        <div class="course-state">
          <span class="state-dot" :class="course?.state === 2 ? 'ongoing' : 'ended'"></span>
          {{ stateLabel }}
        </div>
      </div>
    </div>

    <!-- 活动统计 -->
    <div class="act-stats" v-if="activities.length">
      <div class="act-stat">
        <span class="act-stat-num">{{ ongoingCount }}</span>
        <span class="act-stat-label">进行中</span>
      </div>
      <div class="act-stat-divider"></div>
      <div class="act-stat">
        <span class="act-stat-num">{{ endedCount }}</span>
        <span class="act-stat-label">已结束</span>
      </div>
    </div>

    <!-- 活动列表 -->
    <div class="section-title">活动列表</div>

    <activity-item
      v-for="act in activities"
      :key="act.id"
      :activity="act"
      :face-teach-id="faceTeachId"
      @refresh="refreshActivities"
    />

    <!-- 空状态 -->
    <div v-if="activities.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <div class="empty-text">暂无活动</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getCourseActivities } from '../api/index.js'
import ActivityItem from '../components/ActivityItem.vue'

const route = useRoute()
const faceTeachId = ref(route.params.faceTeachId)
const course = ref(null)
const activities = ref([])

const stateLabel = computed(() => {
  const state = course?.value?.state || 0
  if (state === 2) return '进行中'
  if (state === 3) return '已结束'
  return '未知'
})

const ongoingCount = computed(() => activities.value.filter(a => a.state === 2).length)
const endedCount = computed(() => activities.value.filter(a => a.state === 3).length)

const refreshActivities = async () => {
  try {
    const res = await getCourseActivities(faceTeachId.value)
    if (res.data.code === 200) {
      activities.value = res.data.result || []
      if (activities.value.length > 0) {
        course.value = {
          courseName: route.query.name || activities.value[0].courseName || '课程',
          state: activities.value[0].classState || 2,
        }
      }
    }
  } catch (e) { /* ignore */ }
}

onMounted(() => refreshActivities())

watch(() => route.params.faceTeachId, (newId) => {
  faceTeachId.value = newId
  refreshActivities()
})
</script>

<style scoped>
.course-detail {
  padding-bottom: 80px;
}

/* 课程头部 */
.course-header {
  position: relative;
  overflow: hidden;
}

.course-header-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.course-header.ended .course-header-bg {
  background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
}

.course-header-content {
  position: relative;
  padding: 16px 20px 20px;
}

.back-btn {
  color: rgba(255,255,255,0.9) !important;
  cursor: pointer;
  margin-bottom: 8px;
}

.course-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  line-height: 1.4;
}

.course-state {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255,255,255,0.8);
  margin-top: 6px;
}

.state-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.state-dot.ongoing {
  background: var(--success);
  animation: pulse 2s infinite;
}

.state-dot.ended {
  background: rgba(255,255,255,0.5);
}

/* 统计 */
.act-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 16px;
  margin: 0 16px 4px;
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.act-stat {
  text-align: center;
}

.act-stat-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
}

.act-stat-label {
  font-size: 11px;
  color: var(--text-muted);
}

.act-stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border);
}

/* 分区标题 */
.section-title {
  padding: 16px 20px 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 48px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 14px;
  color: var(--text-muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>