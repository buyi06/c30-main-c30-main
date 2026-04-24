<template>
  <div class="status-indicator">
    <span class="dot" :class="statusClass"></span>
    <span class="label">{{ statusLabel }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'running' },
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
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  position: relative;
}

.dot.green {
  background: var(--success);
  animation: dot-pulse 2s infinite;
}

.dot.green::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: rgba(16, 185, 129, 0.25);
  animation: ring-pulse 2s infinite;
}

.dot.yellow {
  background: var(--warning);
  animation: dot-pulse 3s infinite;
}

.dot.red {
  background: var(--danger);
  animation: dot-pulse 1s infinite;
}

.label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.5); opacity: 0; }
}
</style>