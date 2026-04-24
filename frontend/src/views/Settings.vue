<template>
  <div class="settings-page">
    <!-- 头部 -->
    <div class="settings-header">
      <van-icon name="arrow-left" size="20" class="back-btn" @click="$router.back()" />
      <span class="settings-title">设置</span>
      <span style="width:20px"></span>
    </div>

    <!-- 密码设置 -->
    <div class="settings-section">
      <div class="section-label">🔐 安全设置</div>
      <div class="settings-card">
        <van-field
          v-model="oldPassword"
          type="password"
          label="旧密码"
          placeholder="请输入旧密码"
          clearable
        />
        <van-field
          v-model="newPassword"
          type="password"
          label="新密码"
          placeholder="请输入新密码"
          clearable
        />
        <div class="card-footer">
          <van-button type="primary" size="small" round @click="changePassword">修改密码</van-button>
        </div>
      </div>
    </div>

    <!-- C30账号 -->
    <div class="settings-section">
      <div class="section-label">👤 C30账号</div>
      <div class="settings-card">
        <van-field
          v-model="c30Username"
          label="用户名"
          placeholder="C30平台用户名"
          clearable
        />
        <van-field
          v-model="c30Password"
          type="password"
          label="密码"
          placeholder="C30平台密码"
          clearable
        />
        <div class="card-footer">
          <van-button type="primary" size="small" round @click="saveCredentials">保存账号</van-button>
        </div>
      </div>
    </div>

    <!-- 自动回复 -->
    <div class="settings-section">
      <div class="section-label">🤖 自动回复</div>
      <div class="settings-card">
        <van-field
          v-model="discussContent"
          label="讨论回复"
          type="textarea"
          rows="2"
          autosize
          placeholder="讨论自动回复内容"
        />
        <van-field
          v-model="brainstormContent"
          label="头脑风暴"
          type="textarea"
          rows="2"
          autosize
          placeholder="头脑风暴自动提交内容"
        />
        <div class="card-footer">
          <van-button type="primary" size="small" round @click="saveAutoReply">保存内容</van-button>
        </div>
      </div>
    </div>

    <!-- 轮询间隔 -->
    <div class="settings-section">
      <div class="section-label">⏱️ 轮询间隔</div>
      <div class="settings-card">
        <van-field v-model="pollPreClass" label="课前（秒）" type="number" />
        <van-field v-model="pollInClass" label="课中（秒）" type="number" />
        <van-field v-model="pollBetween" label="课间（秒）" type="number" />
        <van-field v-model="pollWeekend" label="周末（秒）" type="number" />
        <div class="card-footer">
          <van-button type="primary" size="small" round @click="savePollIntervals">保存间隔</van-button>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div class="settings-section">
      <div class="section-label">ℹ️ 关于</div>
      <div class="settings-card about-card">
        <div class="about-item">
          <span class="about-label">版本</span>
          <span class="about-value">v1.0.0</span>
        </div>
        <div class="about-item">
          <span class="about-label">项目</span>
          <span class="about-value">C30 管理面板</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig, updateCredentials, updatePassword } from '../api/index.js'
import { showToast } from '../utils/toast.js'

const oldPassword = ref('')
const newPassword = ref('')
const c30Username = ref('')
const c30Password = ref('')
const discussContent = ref('')
const brainstormContent = ref('')
const pollPreClass = ref(60)
const pollInClass = ref(120)
const pollBetween = ref(1800)
const pollWeekend = ref(7200)

onMounted(async () => {
  try {
    const res = await getConfig()
    if (res.data.code === 200) {
      const cfg = res.data.result
      c30Username.value = cfg.c30_username || ''
      discussContent.value = cfg.auto_discuss_content || ''
      brainstormContent.value = cfg.auto_brainstorm_content || ''
      pollPreClass.value = cfg.poll_intervals?.pre_class || 60
      pollInClass.value = cfg.poll_intervals?.in_class || 120
      pollBetween.value = cfg.poll_intervals?.between || 1800
      pollWeekend.value = cfg.poll_intervals?.weekend || 7200
    }
  } catch (e) { /* ignore */ }
})

const changePassword = async () => {
  if (!oldPassword.value || !newPassword.value) return showToast('请填写完整')
  try {
    const res = await updatePassword({ old_password: oldPassword.value, new_password: newPassword.value })
    if (res.data.code === 200) {
      showToast('密码已更新')
      oldPassword.value = ''
      newPassword.value = ''
    } else {
      showToast(res.data.message || '修改失败')
    }
  } catch (e) { showToast('修改失败') }
}

const saveCredentials = async () => {
  if (!c30Username.value || !c30Password.value) return showToast('请填写完整')
  try {
    const res = await updateCredentials({ c30_username: c30Username.value, c30_password: c30Password.value })
    if (res.data.code === 200) showToast('账号已保存')
    else showToast(res.data.message || '保存失败')
  } catch (e) { showToast('保存失败') }
}

const saveAutoReply = async () => {
  try {
    const res = await updateConfig({
      auto_discuss_content: discussContent.value,
      auto_brainstorm_content: brainstormContent.value,
    })
    if (res.data.code === 200) showToast('内容已保存')
    else showToast(res.data.message || '保存失败')
  } catch (e) { showToast('保存失败') }
}

const savePollIntervals = async () => {
  try {
    const res = await updateConfig({
      poll_intervals: {
        pre_class: parseInt(pollPreClass.value) || 60,
        in_class: parseInt(pollInClass.value) || 120,
        between: parseInt(pollBetween.value) || 1800,
        weekend: parseInt(pollWeekend.value) || 7200,
      },
    })
    if (res.data.code === 200) showToast('间隔已保存')
    else showToast(res.data.message || '保存失败')
  } catch (e) { showToast('保存失败') }
}
</script>

<style scoped>
.settings-page {
  padding-bottom: 80px;
  min-height: 100vh;
  background: var(--bg);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
}

.back-btn {
  cursor: pointer;
  color: var(--text) !important;
}

.settings-title {
  font-size: 17px;
  font-weight: 600;
}

/* 分区 */
.settings-section {
  margin-top: 16px;
}

.section-label {
  padding: 0 20px 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.settings-card {
  margin: 0 16px;
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.card-footer {
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
}

/* 关于 */
.about-card {
  padding: 4px 0;
}

.about-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.about-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.about-value {
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
}
</style>