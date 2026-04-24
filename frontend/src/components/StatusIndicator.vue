<template>
  <div class="status-indicator">
    <span class="dot" :class="statusClass"></span>
    <span class="label">{{ statusLabel }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'running',
  },
})

const statusClass = computed(() => {
  switch (props.status) {
    case 'running': return 'green'
    case 'paused': return 'yellow'
    case 'error': return 'red'
    default: return 'green'
  }
})

const statusLabel = computed(() => {
  switch (props.status) {
    case 'running': return '运行中'
    case 'paused': return '已暂停'
    case 'error': return '异常'
    default: return '运行中'
  }
})
</script>

<style scoped>
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.green {
  background: #07c160;
}

.dot.yellow {
  background: #ff976a;
}

.dot.red {
  background: #ee0a24;
}

.label {
  font-size: 14px;
  color: #646566;
}
</style>