import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const app = createApp(App)

// 配置axios
axios.defaults.baseURL = process.env.NODE_ENV === 'production'
  ? '/api'
  : 'http://localhost:5000/api'

// 添加请求拦截器
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 添加响应拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        // Token过期或无效，清除本地存储并重定向到登录页
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('身份认证失败，请重新登录')
      } else if (error.response.data && error.response.data.message) {
        ElMessage.error(error.response.data.message)
      } else {
        ElMessage.error('服务器错误，请稍后重试')
      }
    } else {
      ElMessage.error('网络错误，请检查您的网络连接')
    }
    return Promise.reject(error)
  }
)

app.config.globalProperties.$http = axios
app.use(store).use(router).use(ElementPlus)
app.mount('#app') 