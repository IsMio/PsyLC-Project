import axios from 'axios'
import { message } from 'ant-design-vue'
import router from '../router'

const service = axios.create({
  baseURL: import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || ''),
  timeout: 100000
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      message.error(res.msg || '请求失败')
      return Promise.reject(new Error(res.msg || 'Error'))
    }
    return res
  },
  (error) => {
    console.error('Response error:', error)
    const status = error.response?.status
    const errorMessage = error.response?.data?.detail || error.response?.data?.msg || '网络错误，请稍后重试'
    if (status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
    }
    if (status === 403) {
      router.push('/403')
    }
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

export default service
