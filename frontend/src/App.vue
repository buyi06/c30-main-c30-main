<template>
  <div class="app-container">
    <!-- 登录弹窗 -->
    <van-dialog
      v-model:show="showLogin"
      title="请输入管理密码"
      show-cancel-button
      @confirm="doLogin"
      @cancel="showLogin = false"
    >
      <van-field
        v-model="loginPassword"
        type="password"
        placeholder="请输入密码"
        autofocus
      />
    </van-dialog>

    <!-- 主内容 -->
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>

    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" route fixed placeholder safe-area-area-bottom>
      <van-tabbar-item to="/" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/logs" icon="records-o">日志</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login } from './api/index.js'

const router = useRouter()
const showLogin = ref(false)
const loginPassword = ref('')
const activeTab = ref(0)

// 检查是否已登录
onMounted(() => {
  const token = localStorage.getItem('c30_token')
  if (!token) {
    showLogin.value = true
  }

  // 监听401事件
  window.addEventListener('auth-required', () => {
    localStorage.removeItem('c30_token')
    showLogin.value = true
  })
})

// 登录
const doLogin = async () => {
  if (!loginPassword.value) return
  try {
    const res = await login(loginPassword.value)
    if (res.data.code === 200) {
      localStorage.setItem('c30_token', res.data.token)
      showLogin.value = false
      loginPassword.value = ''
      showToast('登录成功')
    } else {
      showToast(res.data.message || '登录失败')
    }
  } catch (e) {
    showToast('登录失败')
  }
}

const showToast = (msg) => {
  // 使用 vant showToast
  import('vant').then(({ showToast }) => {
    showToast({ message: msg, duration: 2000 })
  })
}
</script>

<style>
.app-container {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f7f8fa;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>