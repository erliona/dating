import { ref } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: '/v1',
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

  // Auth endpoints
  const validateToken = async (token) => {
    return post('/auth/validate', { token })
  }

  // Profile endpoints
  const getProfile = async () => {
    return get('/profile')
  }

  const updateProfile = async (data) => {
    return put('/profile', data)
  }

  const requestVerification = async (selfieData) => {
    return post('/profile/verification/request', selfieData)
  }

  // Discovery endpoints
  const getCandidates = async (params = {}) => {
    return get('/discovery/candidates', { params })
  }

  const swipeUser = async (userId, action) => {
    return post('/discovery/swipe', { user_id: userId, action })
  }

  const getMatches = async () => {
    return get('/discovery/matches')
  }

  const getLikes = async () => {
    return get('/discovery/likes')
  }

  // Chat endpoints
  const getConversations = async () => {
    return get('/chat/conversations')
  }

  const getMessages = async (conversationId, limit = 50, offset = 0) => {
    return get(`/chat/conversations/${conversationId}/messages`, { 
      params: { limit, offset } 
    })
  }

  const sendMessage = async (conversationId, content, contentType = 'text') => {
    return post('/chat/messages', { 
      conversation_id: conversationId, 
      content, 
      content_type: contentType 
    })
  }

  const markMessageAsRead = async (messageId) => {
    return put(`/chat/messages/${messageId}/read`)
  }

  const blockConversation = async (conversationId) => {
    return post(`/chat/conversations/${conversationId}/block`)
  }

  const reportConversation = async (conversationId, reportType, reason) => {
    return post(`/chat/conversations/${conversationId}/report`, { 
      report_type: reportType, 
      reason 
    })
  }

  // Media endpoints
  const uploadPhoto = async (file, onProgress) => {
    const formData = new FormData()
    formData.append('photo', file)

    return request({
      method: 'POST',
      url: '/media/upload',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    })
  }

  const deletePhoto = async (photoId) => {
    return del(`/media/${photoId}`)
  }

  // Settings endpoints
  const getUserPreferences = async () => {
    return get('/settings/preferences')
  }

  const updateUserPreferences = async (preferences) => {
    return put('/settings/preferences', preferences)
  }

  const getNotificationSettings = async () => {
    return get('/settings/notifications')
  }

  const updateNotificationSettings = async (settings) => {
    return put('/settings/notifications', settings)
  }

  return {
    api,
    loading,
    error,
    request,
    get,
    post,
    put,
    delete: del,
    // Auth
    validateToken,
    // Profile
    getProfile,
    updateProfile,
    requestVerification,
    // Discovery
    getCandidates,
    swipeUser,
    getMatches,
    getLikes,
    // Chat
    getConversations,
    getMessages,
    sendMessage,
    markMessageAsRead,
    blockConversation,
    reportConversation,
    // Media
    uploadPhoto,
    deletePhoto,
    // Settings
    getUserPreferences,
    updateUserPreferences,
    getNotificationSettings,
    updateNotificationSettings
  }
}
