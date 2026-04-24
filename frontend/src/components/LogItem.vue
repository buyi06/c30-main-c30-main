<template>
  <div class="log-item">
    <span class="time">{{ log.timestamp }}</span>
    <span class="dot" :class="levelClass"></span>
    <span class="message">{{ log.message }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  log: {
    type: Object,
    required: true,
  },
})

const levelClass = computed(() => {
  switch (props.log.level) {
    case 'success': return 'green'
    case 'info': return 'blue'
    case 'error': return 'red'
    default: return 'blue'
  }
})
</script>

<style scoped>
.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.time {
  color: #969799;
  font-size: 12px;
  flex-shrink: 0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.dot.green {
  background: #07c160;
}

.dot.blue {
  background: #1989fa;
}

.dot.red {
  background: #ee0a24;
}

.message {
  color: #323233;
  word-break: break-all;
}
</style>