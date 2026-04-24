<template>
  <div class="log-item">
    <span class="log-level-badge" :class="levelClass">{{ levelEmoji }}</span>
    <span class="log-time">{{ shortTime }}</span>
    <span class="log-msg">{{ log.message }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  log: { type: Object, required: true },
})

const levelClass = computed(() => {
  switch (props.log.level) {
    case 'success': return 'green'
    case 'info': return 'blue'
    case 'error': return 'red'
    default: return 'blue'
  }
})

const levelEmoji = computed(() => {
  switch (props.log.level) {
    case 'success': return '✓'
    case 'error': return '✗'
    default: return '›'
  }
})

const shortTime = computed(() => {
  const ts = props.log.timestamp || ''
  // "2026-04-24 22:01:08" -> "22:01:08"
  return ts.split(' ').pop() || ts
})
</script>

<style scoped>
.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
  line-height: 1.5;
}

.log-level-badge {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  margin-top: 1px;
}

.log-level-badge.green {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.log-level-badge.blue {
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.log-level-badge.red {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.log-time {
  color: #6c7086;
  font-size: 12px;
  flex-shrink: 0;
}

.log-msg {
  color: #cdd6f4;
  word-break: break-all;
}
</style>