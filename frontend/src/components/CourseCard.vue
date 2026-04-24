<template>
  <van-card
    :title="course.courseName"
    :thumb="thumbUrl"
    class="course-card"
    @click="$emit('click')"
  >
    <template #desc>
      <div class="course-info">
        <van-tag :type="stateTagType" size="small">{{ stateLabel }}</van-tag>
        <span v-if="course.startTime" class="time">{{ course.startTime }} - {{ course.endTime }}</span>
      </div>
    </template>
  </van-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  course: {
    type: Object,
    required: true,
  },
})

defineEmits(['click'])

const thumbUrl = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect fill="%231989fa" width="40" height="40" rx="4"/><text x="50%" y="55%" fill="white" font-size="20" text-anchor="middle" dominant-baseline="middle">📚</text></svg>'

const stateLabel = computed(() => {
  const state = props.course.state || 0
  if (state === 2) return '进行中'
  if (state === 3) return '已结束'
  return '未开始'
})

const stateTagType = computed(() => {
  const state = props.course.state || 0
  if (state === 2) return 'success'
  if (state === 3) return 'default'
  return 'primary'
})
</script>

<style scoped>
.course-card {
  margin-bottom: 12px;
  cursor: pointer;
}

.course-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time {
  font-size: 12px;
  color: #969799;
}
</style>