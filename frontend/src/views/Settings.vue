<template>
  <div class="settings-page">
    <!-- 返回按钮 -->
    <van-nav-bar title="设置" left-arrow @click-left="$router.back()" />

    <!-- 密码设置 -->
    <van-cell-group inset title="管理密码">
      <van-field
        v-model="oldPassword"
        type="password"
        label="旧密码"
        placeholder="请输入旧密码"
      />
      <van-field
        v-model="newPassword"
        type="password"
        label="新密码"
        placeholder="请输入新密码"
      />
      <van-cell>
        <van-button type="primary" size="small" @click="changePassword">修改密码</van-button>
      </van-cell>
    </van-cell-group>

    <!-- C30账号 -->
    <van-cell-group inset title="C30账号">
      <van-field
        v-model="c30Username"
        label="用户名"
        placeholder="C30平台用户名"
      />
      <van-field
        v-model="c30Password"
        type="password"
        label="密码"
        placeholder="C30平台密码"
      />
      <van-cell>
        <van-button type="primary" size="small" @click="saveCredentials">保存账号</van-button>
      </van-cell>
    </van-cell-group>

    <!-- 自动回复 -->
    <van-cell-group inset title="自动回复内容">
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
      <van-cell>
        <van-button type="primary" size="small" @click="saveAutoReply">保存内容</van-button>
      </van-cell>
    </van-cell-group>

    <!-- 轮询间隔 -->
    <van-cell-group inset title="轮询间隔（秒）">
      <van-field v-model="pollPreClass" label="课前" type="number" />
      <van-field v-model="pollInClass" label="课中" type="number" />
      <van-field v-model="pollBetween" label="课间" type="number" />
      <van-field v-model="pollWeekend" label="周末" type="number" />
      <van-cell>
        <van-button type="primary" size="small" @click="savePollIntervals">保存间隔</van-button>
      </van-cell>
    </van-cell-group>

    <!-- 关于 -->
    <van-cell-group inset title="关于">
      <van-cell title="版本" value="1.0.0" />
      <van-cell title="项目" value="C30管理面板" />
    </van-cell-group>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig, updateCredentials, updatePassword } from '../api/index.js'

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

// 加载配置
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

const showToast = (msg) => {
  import('vant').then(({ showToast }) => {
    showToast({ message: msg, duration: 2000 })
  })
}

const changePassword = async () => {
  if (!oldPassword.value || !newPassword.value) {
    showToast('请填写完整')
    return
  }
  try {
    const res = await updatePassword({ old_password: oldPassword.value, new_password: newPassword.value })
    if (res.data.code === 200) {
      showToast('密码已更新')
      oldPassword.value = ''
      newPassword.value = ''
    } else {
      showToast(res.data.message || '修改失败')
    }
  } catch (e) {
    showToast('修改失败')
  }
}

const saveCredentials = async () => {
  if (!c30Username.value || !c30Password.value) {
    showToast('请填写完整')
    return
  }
  try {
    const res = await updateCredentials({ c30_username: c30Username.value, c30_password: c30Password.value })
    if (res.data.code === 200) {
      showToast('账号已保存')
    } else {
      showToast(res.data.message || '保存失败')
    }
  } catch (e) {
    showToast('保存失败')
  }
}

const saveAutoReply = async () => {
  try {
    const res = await updateConfig({
      auto_discuss_content: discussContent.value,
      auto_brainstorm_content: brainstormContent.value,
    })
    if (res.data.code === 200) {
      showToast('内容已保存')
    } else {
      showToast(res.data.message || '保存失败')
    }
  } catch (e) {
    showToast('保存失败')
  }
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
    if (res.data.code === 200) {
      showToast('间隔已保存')
    } else {
      showToast(res.data.message || '保存失败')
    }
  } catch (e) {
    showToast('保存失败')
  }
}
</script>

<style scoped>
.settings-page {
  padding-bottom: 60px;
}
</style>