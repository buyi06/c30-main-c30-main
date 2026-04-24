import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器 - 自动携带JWT
http.interceptors.request.use(config => {
  const token = localStorage.getItem('c30_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - 401时清除token
http.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('c30_token')
      // 触发全局事件让App.vue显示登录弹窗
      window.dispatchEvent(new CustomEvent('auth-required'))
    }
    return Promise.reject(error)
  }
)

// ===== 认证 =====
export const login = (password) => http.post('/auth/login', { password })

// ===== 状态 =====
export const getStatus = () => http.get('/status')
export const getCoursesToday = () => http.get('/courses/today')
export const getCourseActivities = (faceTeachId) => http.get(`/courses/${faceTeachId}/activities`)
export const getActivityDetail = (activityId) => http.get(`/activities/${activityId}/detail`)

// ===== 操作 =====
export const manualSign = (activityId) => http.post(`/actions/sign/${activityId}`)
export const manualDiscuss = (activityId, content) => http.post(`/actions/discuss/${activityId}`, { content })
export const manualBrainstorm = (activityId, content) => http.post(`/actions/brainstorm/${activityId}`, { content })
export const manualVote = (activityId, options) => http.post(`/actions/vote/${activityId}`, { options })
export const manualRefresh = () => http.post('/actions/refresh')

// ===== 配置 =====
export const getConfig = () => http.get('/config')
export const updateConfig = (data) => http.put('/config', data)
export const updateCredentials = (data) => http.put('/config/credentials', data)
export const updatePassword = (data) => http.put('/config/password', data)

// ===== 调度 =====
export const schedulerPause = () => http.post('/scheduler/pause')
export const schedulerResume = () => http.post('/scheduler/resume')
export const getSchedulerJobs = () => http.get('/scheduler/jobs')

export default http