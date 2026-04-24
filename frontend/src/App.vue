<template>
  <div class="app-container">
    <!-- 登录弹窗 -->
    <van-overlay :show="showLogin" class="login-overlay">
      <div class="login-wrapper" @click.stop>
        <div class="login-card">
          <div class="login-header">
            <div class="login-logo">📚</div>
            <div class="login-title">C30 管理面板</div>
            <div class="login-subtitle">请输入管理密码以继续</div>
          </div>
          <van-field
            v-model="loginPassword"
            type="password"
            placeholder="请输入密码"
            autofocus
            class="login-input"
            @keyup.enter="doLogin"
          >
            <template #left-icon>
              <van-icon name="lock" color="#6366f1" />
            </template>
          </van-field>
          <van-button type="primary" block round class="login-btn" @click="doLogin" :loading="loginLoading">
            登 录
          </van-button>
        </div>
      </div>
    </van-overlay>

    <!-- 主内容 -->
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>

    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" route fixed placeholder safe-area-area-bottom class="app-tabbar">
      <van-tabbar-item to="/" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/logs" icon="records-o">日志</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { login } from './api/index.js'
import { showToast } from './utils/toast.js'

const showLogin = ref(false)
const loginPassword = ref('')
const loginLoading = ref(false)
const activeTab = ref(0)

onMounted(() => {
  const token = localStorage.getItem('c30_token')
  if (!token) {
    showLogin.value = true
  }
  window.addEventListener('auth-required', () => {
    localStorage.removeItem('c30_token')
    showLogin.value = true
  })
})

const doLogin = async () => {
  if (!loginPassword.value) return
  loginLoading.value = true
  try {
    const res = await login(loginPassword.value)
    if (res.data.code === 200) {
      localStorage.setItem('c30_token', res.data.token)
      showLogin.value = false
      loginPassword.value = ''
      showToast('登录成功')
    } else {
      showToast(res.data.message || '密码错误')
    }
  } catch (e) {
    showToast('登录失败')
  } finally {
    loginLoading.value = false
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --primary: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --primary-bg: #eef2ff;
  --success: #10b981;
  --success-light: #d1fae5;
  --warning: #f59e0b;
  --warning-light: #fef3c7;
  --danger: #ef4444;
  --danger-light: #fee2e2;
  --info: #3b82f6;
  --info-light: #dbeafe;
  --bg: #f0f2f5;
  --card: #ffffff;
  --text: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
  --radius: 12px;
  --radius-sm: 8px;
  --radius-lg: 16px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  position: relative;
  background: var(--bg);
}

/* Vant 覆盖样式 */
.van-button--primary {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
  border: none !important;
  font-weight: 600;
}

.van-tabbar {
  border-top: 1px solid var(--border) !important;
  box-shadow: 0 -1px 8px rgba(0,0,0,0.04);
}

.van-tabbar-item--active {
  color: var(--primary) !important;
}

/* 登录弹窗 */
.login-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  padding: 24px;
}

.login-card {
  background: var(--card);
  border-radius: var(--radius-lg);
  padding: 32px 24px;
  width: 100%;
  max-width: 340px;
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-logo {
  font-size: 48px;
  margin-bottom: 12px;
}

.login-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.login-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

.login-input {
  margin-bottom: 20px;
}

.login-input .van-field__control {
  font-size: 15px;
}

.login-btn {
  height: 44px;
  font-size: 16px;
}

/* Vant 全局微调 */
.van-cell-group--inset {
  margin: 12px 16px !important;
  border-radius: var(--radius) !important;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.van-collapse-item {
  margin: 0 16px 8px;
  border-radius: var(--radius) !important;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.van-empty__description {
  color: var(--text-muted);
}

.van-nav-bar {
  background: transparent !important;
}

.van-nav-bar__title {
  font-weight: 600 !important;
  color: var(--text) !important;
}
</style>