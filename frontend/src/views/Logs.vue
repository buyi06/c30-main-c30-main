<template>
  <div class="logs-page">
    <!-- 日志头部 -->
    <div class="logs-header">
      <div class="logs-header-title">实时日志</div>
      <div class="logs-header-dot" :class="{ connected: wsConnected }"></div>
    </div>

    <!-- 筛选Tab -->
    <div class="filter-bar">
      <div
        v-for="f in filters"
        :key="f.key"
        class="filter-chip"
        :class="{ active: activeFilter === f.key }"
        @click="activeFilter = f.key"
      >
        <span class="filter-emoji">{{ f.emoji }}</span>
        {{ f.label }}
      </div>
    </div>

    <!-- 日志列表 -->
    <div class="logs-container" ref="logsContainer">
      <div v-if="filteredLogs.length === 0" class="empty-logs">
        <div class="empty-icon">📋</div>
        <div class="empty-text">暂无日志</div>
      </div>
      <log-item
        v-for="log in filteredLogs"
        :key="log.timestamp + log.message"
        :log="log"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import ws from '../utils/ws.js'
import LogItem from '../components/LogItem.vue'

const activeFilter = ref('all')
const logs = ref([])
const logsContainer = ref(null)
const wsConnected = ref(false)

const filters = [
  { key: 'all', label: '全部', emoji: '📌' },
  { key: 'sign', label: '签到', emoji: '✅' },
  { key: 'discuss', label: '讨论', emoji: '💬' },
  { key: 'brainstorm', label: '头脑风暴', emoji: '💡' },
  { key: 'vote', label: '投票', emoji: '🗳️' },
  { key: 'error', label: '错误', emoji: '❌' },
]

const filteredLogs = computed(() => {
  if (activeFilter.value === 'all') return logs.value
  if (activeFilter.value === 'error') return logs.value.filter(l => l.level === 'error')
  return logs.value.filter(l => l.category === activeFilter.value)
})

const scrollToBottom = () => {
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  ws.connect()
  wsConnected.value = true

  ws.onMessage((entry) => {
    logs.value.push(entry)
    if (logs.value.length > 500) logs.value.shift()
    scrollToBottom()
  })

  // 连接状态检测
  const checkConn = setInterval(() => {
    wsConnected.value = ws.ws?.readyState === WebSocket.OPEN
  }, 2000)
  onUnmounted(() => clearInterval(checkConn))
})

onUnmounted(() => {
  ws.disconnect()
})
</script>

<style scoped>
.logs-page {
  padding-bottom: 80px;
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 8px;
}

.logs-header-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.logs-header-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  transition: background 0.3s;
}

.logs-header-dot.connected {
  background: var(--success);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

/* 筛选条 */
.filter-bar {
  display: flex;
  gap: 6px;
  padding: 4px 16px 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.filter-bar::-webkit-scrollbar {
  display: none;
}

.filter-chip {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--card);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-chip.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.filter-emoji {
  font-size: 12px;
}

/* 日志容器 - 终端风格 */
.logs-container {
  margin: 0 16px;
  padding: 12px;
  max-height: calc(100vh - 170px);
  overflow-y: auto;
  background: #1e1e2e;
  border-radius: var(--radius);
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  -webkit-overflow-scrolling: touch;
}

.empty-logs {
  text-align: center;
  padding: 32px 0;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 13px;
  color: #6c7086;
}
</style>