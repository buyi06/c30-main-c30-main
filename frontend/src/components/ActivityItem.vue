<template>
  <van-collapse-item :title="title" :name="activity.id">
    <template #title>
      <div class="activity-title">
        <van-icon :name="iconName" class="activity-icon" />
        <span>{{ typeLabel }}</span>
        <span class="activity-name">{{ activity.title || '未命名' }}</span>
        <van-tag :type="stateTagType" size="small">{{ stateLabel }}</van-tag>
      </div>
    </template>

    <!-- 签到详情 -->
    <div v-if="activity.activityType === 1 || activity.activityType === 9" class="activity-detail">
      <van-cell-group inset>
        <van-cell title="签到模式" :value="activityPattern" />
        <van-cell title="签到状态" :value="signStatusLabel" />
      </van-cell-group>
      <van-button
        type="primary"
        size="small"
        block
        @click="doSign"
        :disabled="activity.state !== 2"
      >
        手动签到
      </van-button>
    </div>

    <!-- 讨论详情 -->
    <div v-if="activity.activityType === 2" class="activity-detail">
      <van-field
        v-model="discussInput"
        label="回复内容"
        type="textarea"
        rows="2"
        autosize
        placeholder="输入回复内容"
      />
      <van-button
        type="primary"
        size="small"
        block
        @click="doDiscuss"
        :disabled="activity.state !== 2"
      >
        手动回复
      </van-button>
    </div>

    <!-- 头脑风暴详情 -->
    <div v-if="activity.activityType === 4" class="activity-detail">
      <van-field
        v-model="brainstormInput"
        label="提交内容"
        type="textarea"
        rows="2"
        autosize
        placeholder="输入观点内容"
      />
      <van-button
        type="primary"
        size="small"
        block
        @click="doBrainstorm"
        :disabled="activity.state !== 2"
      >
        手动提交
      </van-button>
    </div>

    <!-- 投票详情 -->
    <div v-if="activity.activityType === 3" class="activity-detail">
      <van-checkbox-group v-model="voteSelected">
        <van-cell-group inset>
          <van-cell
            v-for="opt in voteOptions"
            :key="opt.sortOrder"
            clickable
            @click="toggleVote(opt.sortOrder)"
          >
            <template #title>
              <van-checkbox :name="opt.sortOrder" ref="checkboxes">
                {{ opt.optionContent || opt.content || '选项' + opt.sortOrder }}
              </van-checkbox>
            </template>
          </van-cell>
        </van-cell-group>
      </van-checkbox-group>
      <van-button
        type="primary"
        size="small"
        block
        @click="doVote"
        :disabled="activity.state !== 2 || voteSelected.length === 0"
      >
        手动投票
      </van-button>
    </div>
  </van-collapse-item>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { manualSign, manualDiscuss, manualBrainstorm, manualVote, getActivityDetail } from '../api/index.js'

const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
  faceTeachId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['refresh'])

const discussInput = ref('')
const brainstormInput = ref('')
const voteSelected = ref([])
const voteOptions = ref([])
const signStatus = ref(-1)
const signPatternData = ref('')
const activityPattern = ref('普通')

// 类型图标和标签
const iconName = computed(() => {
  const type = props.activity.activityType
  switch (type) {
    case 1: return 'success'
    case 2: return 'chat-o'
    case 3: return 'thumb-circle-o'
    case 4: return 'bulb-o'
    case 9: return 'cross'
    default: return 'info-o'
  }
})

const typeLabel = computed(() => {
  const map = { 1: '签到', 2: '讨论', 3: '投票', 4: '头脑风暴', 9: '签退' }
  return map[props.activity.activityType] || '其他'
})

const title = computed(() => props.activity.title || '活动')

// 状态标签
const stateLabel = computed(() => {
  const state = props.activity.state || 0
  if (state === 2) return '进行中'
  if (state === 3) return '已结束'
  return '未知'
})

const stateTagType = computed(() => {
  const state = props.activity.state || 0
  if (state === 2) return 'success'
  if (state === 3) return 'default'
  return 'primary'
})

const signStatusLabel = computed(() => {
  if (signStatus.value === 1) return '已签到'
  if (signStatus.value === 0) return '未签到'
  return '未知'
})

// 加载详情
onMounted(async () => {
  try {
    const res = await getActivityDetail(props.activity.id)
    if (res.data.code === 200) {
      const detail = res.data.result
      if (props.activity.activityType === 1 || props.activity.activityType === 9) {
        signStatus.value = detail.signStatus
        signPatternData.value = detail.signDetail?.signPatternData || ''
        activityPattern.value = detail.pattern || '普通'
      }
      if (props.activity.activityType === 3) {
        const optData = detail.voteDetail?.optionData
        if (typeof optData === 'string') {
          try {
            voteOptions.value = JSON.parse(optData)
          } catch (e) {
            voteOptions.value = []
          }
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
    if (res.data.code === 200) {
      showToast('签到成功')
      emit('refresh')
    } else {
      showToast(res.data.message || '失败')
    }
  } catch (e) {
    showToast('签到失败')
  }
}

const doDiscuss = async () => {
  try {
    const content = discussInput.value || ''
    const res = await manualDiscuss(props.activity.id, content)
    if (res.data.code === 200) {
      showToast('回复成功')
      emit('refresh')
    } else {
      showToast(res.data.message || '失败')
    }
  } catch (e) {
    showToast('回复失败')
  }
}

const doBrainstorm = async () => {
  try {
    const content = brainstormInput.value || ''
    const res = await manualBrainstorm(props.activity.id, content)
    if (res.data.code === 200) {
      showToast('提交成功')
      emit('refresh')
    } else {
      showToast(res.data.message || '失败')
    }
  } catch (e) {
    showToast('提交失败')
  }
}

const toggleVote = (sortOrder) => {
  const idx = voteSelected.value.indexOf(sortOrder)
  if (idx === -1) {
    voteSelected.value.push(sortOrder)
  } else {
    voteSelected.value.splice(idx, 1)
  }
}

const doVote = async () => {
  try {
    const options = voteSelected.value.join(',')
    const res = await manualVote(props.activity.id, options)
    if (res.data.code === 200) {
      showToast('投票成功')
      emit('refresh')
    } else {
      showToast(res.data.message || '失败')
    }
  } catch (e) {
    showToast('投票失败')
  }
}
</script>

<style scoped>
.activity-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.activity-icon {
  font-size: 16px;
}

.activity-name {
  font-weight: 500;
}

.activity-detail {
  padding: 8px 0;
}
</style>