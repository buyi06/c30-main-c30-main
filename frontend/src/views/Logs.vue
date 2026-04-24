<template>
  <div class="logs-page">
    <!-- 筛选Tab -->
    <van-tabs v-model:active="activeFilter" sticky shrink>
      <van-tab title="全部" name="all" />
      <van-tab title="签到" name="sign" />
      <van-tab title="讨论" name="discuss" />
      <van-tab title="头脑风暴" name="brainstorm" />
      <van-tab title="投票" name="vote" />
      <van-tab title="错误" name="error" />
    </van-tabs>

    <!-- 日志列表 -->
    <div class="logs-container" ref="logsContainer">
      <log-item
        v-for="log in filteredLogs"
        :key="log.timestamp + log.message"
        :log="log"
      />
      <van-empty v-if="filteredLogs.length === 0" description="暂无日志" />
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

// 筛选后的日志
const filteredLogs = computed(() => {
  if (activeFilter.value === 'all') {
    return logs.value
  }
  if (activeFilter.value === 'error') {
    return logs.value.filter(l => l.level === 'error')
  }
  return logs.value.filter(l => l.category === activeFilter.value)
})

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  ws.connect()
  ws.onMessage((entry) => {
    logs.value.push(entry)
    // 限制最大500条
    if (logs.value.length > 500) {
      logs.value.shift()
    }
    scrollToBottom()
  })
})

onUnmounted(() => {
  ws.disconnect()
})
</script>

<style scoped>
.logs-page {
  padding-bottom: 60px;
}

.logs-container {
  padding: 16px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}
</style>