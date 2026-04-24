<template>
  <div class="activity-card">
    <div class="activity-header" @click="expanded = !expanded">
      <div class="activity-type-badge" :style="typeBadgeStyle">
        {{ typeEmoji }}
      </div>
      <div class="activity-info">
        <div class="activity-name">{{ activity.title || typeLabel }}</div>
        <div class="activity-meta">
          <span class="meta-type">{{ typeLabel }}</span>
          <span class="meta-dot">·</span>
          <van-tag :type="stateTagType" size="small" round>{{ stateLabel }}</van-tag>
        </div>
      </div>
      <van-icon :name="expanded ? 'arrow-up' : 'arrow-down'" size="14" color="#94a3b8" />
    </div>

    <!-- 展开内容 -->
    <div class="activity-body" v-if="expanded">
      <!-- 签到 -->
      <div v-if="activity.activityType === 1 || activity.activityType === 9" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">签到模式</span>
          <span class="detail-value">{{ activityPattern }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">签到状态</span>
          <span class="detail-value" :class="signStatusLabel === '已签到' ? 'text-success' : 'text-warn'">
            {{ signStatusLabel }}
          </span>
        </div>
        <van-button
          type="primary"
          size="small"
          round
          block
          @click="doSign"
          :disabled="activity.state !== 2"
          class="action-btn"
        >
          手动签到
        </van-button>
      </div>

      <!-- 讨论 -->
      <div v-if="activity.activityType === 2" class="detail-content">
        <van-field
          v-model="discussInput"
          type="textarea"
          rows="2"
          autosize
          placeholder="输入回复内容..."
          class="input-field"
        />
        <van-button
          type="primary"
          size="small"
          round
          block
          @click="doDiscuss"
          :disabled="activity.state !== 2"
          class="action-btn"
        >
          手动回复
        </van-button>
      </div>

      <!-- 头脑风暴 -->
      <div v-if="activity.activityType === 4" class="detail-content">
        <van-field
          v-model="brainstormInput"
          type="textarea"
          rows="2"
          autosize
          placeholder="输入观点内容..."
          class="input-field"
        />
        <van-button
          type="primary"
          size="small"
          round
          block
          @click="doBrainstorm"
          :disabled="activity.state !== 2"
          class="action-btn"
        >
          手动提交
        </van-button>
      </div>

      <!-- 投票 -->
      <div v-if="activity.activityType === 3" class="detail-content">
        <div v-for="opt in voteOptions" :key="opt.sortOrder" class="vote-option"
          :class="{ selected: voteSelected.includes(opt.sortOrder) }"
          @click="toggleVote(opt.sortOrder)"
        >
          <span class="vote-check">
            <van-icon v-if="voteSelected.includes(opt.sortOrder)" name="success" size="14" />
          </span>
          <span>{{ opt.optionContent || opt.content || '选项' + opt.sortOrder }}</span>
        </div>
        <van-button
          type="primary"
          size="small"
          round
          block
          @click="doVote"
          :disabled="activity.state !== 2 || voteSelected.length === 0"
          class="action-btn"
        >
          手动投票
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { manualSign, manualDiscuss, manualBrainstorm, manualVote, getActivityDetail } from '../api/index.js'

const props = defineProps({
  activity: { type: Object, required: true },
  faceTeachId: { type: String, default: '' },
})

const emit = defineEmits(['refresh'])

const expanded = ref(false)
const discussInput = ref('')
const brainstormInput = ref('')
const voteSelected = ref([])
const voteOptions = ref([])
const signStatus = ref(-1)
const activityPattern = ref('普通')

const typeEmoji = computed(() => {
  const map = { 1: '✋', 2: '💬', 3: '🗳️', 4: '💡', 9: '👋' }
  return map[props.activity.activityType] || '📋'
})

const typeLabel = computed(() => {
  const map = { 1: '签到', 2: '讨论', 3: '投票', 4: '头脑风暴', 9: '签退' }
  return map[props.activity.activityType] || '其他'
})

const typeBadgeStyle = computed(() => {
  const map = {
    1: 'background: rgba(16,185,129,0.12); color: #10b981;',
    2: 'background: rgba(59,130,246,0.12); color: #3b82f6;',
    3: 'background: rgba(245,158,11,0.12); color: #f59e0b;',
    4: 'background: rgba(168,85,247,0.12); color: #a855f7;',
    9: 'background: rgba(239,68,68,0.12); color: #ef4444;',
  }
  return map[props.activity.activityType] || 'background: #f1f5f9; color: #64748b;'
})

const stateLabel = computed(() => {
  const s = props.activity.state || 0
  if (s === 2) return '进行中'
  if (s === 3) return '已结束'
  return '未知'
})

const stateTagType = computed(() => {
  const s = props.activity.state || 0
  if (s === 2) return 'success'
  if (s === 3) return 'default'
  return 'primary'
})

const signStatusLabel = computed(() => {
  if (signStatus.value === 1) return '已签到'
  if (signStatus.value === 0) return '未签到'
  return '未知'
})

onMounted(async () => {
  try {
    const res = await getActivityDetail(props.activity.id)
    if (res.data.code === 200) {
      const detail = res.data.result
      if (props.activity.activityType === 1 || props.activity.activityType === 9) {
        signStatus.value = detail.signStatus
        activityPattern.value = detail.pattern || '普通'
      }
      if (props.activity.activityType === 3) {
        const optData = detail.voteDetail?.optionData
        if (typeof optData === 'string') {
          try { voteOptions.value = JSON.parse(optData) } catch (e) { voteOptions.value = [] }
        } else {
          voteOptions.value = optData || []
        }
      }
    }
  } catch (e) { /* ignore */ }
})

const showToast = (msg) => {
  import('vant').then(({ showToast }) => {
    showToast({ message: msg, duration: 2000 })
  })
}

const doSign = async () => {
  try {
    const res = await manualSign(props.activity.id)
    if (res.data.code === 200) { showToast('签到成功'); emit('refresh') }
    else showToast(res.data.message || '失败')
  } catch (e) { showToast('签到失败') }
}

const doDiscuss = async () => {
  try {
    const res = await manualDiscuss(props.activity.id, discussInput.value)
    if (res.data.code === 200) { showToast('回复成功'); emit('refresh') }
    else showToast(res.data.message || '失败')
  } catch (e) { showToast('回复失败') }
}

const doBrainstorm = async () => {
  try {
    const res = await manualBrainstorm(props.activity.id, brainstormInput.value)
    if (res.data.code === 200) { showToast('提交成功'); emit('refresh') }
    else showToast(res.data.message || '失败')
  } catch (e) { showToast('提交失败') }
}

const toggleVote = (sortOrder) => {
  const idx = voteSelected.value.indexOf(sortOrder)
  if (idx === -1) voteSelected.value.push(sortOrder)
  else voteSelected.value.splice(idx, 1)
}

const doVote = async () => {
  try {
    const res = await manualVote(props.activity.id, voteSelected.value.join(','))
    if (res.data.code === 200) { showToast('投票成功'); emit('refresh') }
    else showToast(res.data.message || '失败')
  } catch (e) { showToast('投票失败') }
}
</script>

<style scoped>
.activity-card {
  margin: 0 16px 10px;
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.activity-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
}

.activity-type-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.activity-info {
  flex: 1;
  min-width: 0;
}

.activity-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}

.meta-type {
  font-size: 12px;
  color: var(--text-muted);
}

.meta-dot {
  color: var(--text-muted);
  font-size: 10px;
}

/* 展开内容 */
.activity-body {
  border-top: 1px solid var(--border);
  padding: 14px 16px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 13px;
  color: var(--text-muted);
}

.detail-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}

.text-success { color: var(--success) !important; }
.text-warn { color: var(--warning) !important; }

.input-field {
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.action-btn {
  margin-top: 4px;
}

/* 投票选项 */
.vote-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg);
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
  color: var(--text);
}

.vote-option.selected {
  background: var(--primary-bg);
  color: var(--primary);
}

.vote-check {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.vote-option.selected .vote-check {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
}
</style>