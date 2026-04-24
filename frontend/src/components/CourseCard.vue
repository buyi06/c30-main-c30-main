<template>
  <div class="course-card" @click="$emit('click')">
    <div class="card-accent" :class="stateClass"></div>
    <div class="card-body">
      <div class="card-top">
        <div class="card-title">{{ course.courseName }}</div>
        <van-tag :type="stateTagType" size="medium" round>{{ stateLabel }}</van-tag>
      </div>
      <div class="card-meta">
        <span class="meta-item" v-if="course.address">
          <van-icon name="location-o" size="13" />
          {{ course.address }}
        </span>
        <span class="meta-item">
          <van-icon name="orders-o" size="13" />
          {{ course.activityCount || 0 }} 个活动
        </span>
        <span class="meta-item" v-if="course.classSection">
          <van-icon name="clock-o" size="13" />
          第{{ course.classSection }}节
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  course: { type: Object, required: true },
})

defineEmits(['click'])

const stateLabel = computed(() => {
  const s = props.course.state || 0
  if (s === 2) return '进行中'
  if (s === 3) return '已结束'
  return '未开始'
})

const stateTagType = computed(() => {
  const s = props.course.state || 0
  if (s === 2) return 'success'
  if (s === 3) return 'default'
  return 'primary'
})

const stateClass = computed(() => {
  const s = props.course.state || 0
  if (s === 2) return 'ongoing'
  if (s === 3) return 'ended'
  return 'upcoming'
})
</script>

<style scoped>
.course-card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  margin-bottom: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.course-card:active {
  transform: scale(0.98);
  box-shadow: var(--shadow-md);
}

.card-accent {
  height: 3px;
}

.card-accent.ongoing {
  background: linear-gradient(90deg, var(--success), #34d399);
}

.card-accent.ended {
  background: linear-gradient(90deg, #94a3b8, #cbd5e1);
}

.card-accent.upcoming {
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
}

.card-body {
  padding: 14px 16px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.4;
  flex: 1;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--text-muted);
}
</style>