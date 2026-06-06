import axios from 'axios'

// API 通过 Vercel rewrite 代理到服务器，使用相对路径避免 Mixed Content
const API_BASE = ''
// 生产环境队标使用服务器URL
const LOGO_BASE = window.location.hostname === 'bet365cn.top'
  ? 'http://125.65.79.20:888'
  : ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 JWT
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 自动跳转登录
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      const path = window.location.hash
      if (!path.includes('/admin') && !path.includes('/login')) {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
