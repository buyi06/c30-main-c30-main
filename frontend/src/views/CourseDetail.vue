<template>
  <div class="course-detail">
    <!-- 课程信息 -->
    <van-cell-group inset>
      <van-cell title="课程名称" :value="course?.courseName || '加载中...'" />
      <van-cell title="课堂状态" :value="stateLabel" />
    </van-cell-group>

    <!-- 活动列表 -->
    <div class="section-title">活动列表</div>

    <van-collapse v-model="activeCollapse">
      <activity-item
        v-for="act in activities"
        :key="act.id"
        :activity="act"
        :face-teach-id="faceTeachId"
        @refresh="refreshActivities"
      />
    </van-collapse>

    <!-- 空状态 -->
    <van-empty v-if="activities.length === 0" description="暂无活动" />
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
const activeCollapse = ref([])

const stateLabel = computed(() => {
  const state = course?.value?.state || 0
  if (state === 2) return '进行中'
  if (state === 3) return '已结束'
  return '未知'
})

const refreshActivities = async () => {
  try {
    const res = await getCourseActivities(faceTeachId.value)
    if (res.data.code === 200) {
      activities.value = res.data.result || []
      // 从课程列表推断课程信息（简化）
      if (activities.value.length > 0) {
        course.value = {
          courseName: activities.value[0].courseName || route.query.name || '课程',
          state: activities.value[0].classState || 2,
        }
      }
    }
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  refreshActivities()
})

watch(() => route.params.faceTeachId, (newId) => {
  faceTeachId.value = newId
  refreshActivities()
})
</script>

<style scoped>
.course-detail {
  padding: 16px;
}

.section-title {
  padding: 16px 0 8px;
  font-size: 14px;
  color: #646566;
}
</style>