import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('jwt_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  const request = async (config) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api(config)
      return response
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const get = (url, config = {}) => request({ ...config, method: 'GET', url })
  const post = (url, data, config = {}) => request({ ...config, method: 'POST', url, data })
  const put = (url, data, config = {}) => request({ ...config, method: 'PUT', url, data })
  const del = (url, config = {}) => request({ ...config, method: 'DELETE', url })

  return {
    api,
    loading,
    error,
    request,
    get,
    post,
    put,
    delete: del
  }
}
