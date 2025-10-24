import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const profile = ref(null)
  const preferences = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const { api } = useApi()

  const isAuthenticated = computed(() => !!user.value)
  const isProfileComplete = computed(() => {
    if (!profile.value) return false
    return profile.value.is_complete
  })

  const profileCompletionPercentage = computed(() => {
    if (!profile.value) return 0
    
    let score = 0
    const fields = [
      'name', 'birth_date', 'gender', 'orientation', 'goal', 
      'bio', 'interests', 'height_cm', 'education', 'profession'
    ]
    
    fields.forEach(field => {
      if (profile.value[field]) score += 10
    })
    
    // Photos (30 points total)
    if (profile.value.photos && profile.value.photos.length >= 3) {
      score += 30
    } else if (profile.value.photos && profile.value.photos.length > 0) {
      score += profile.value.photos.length * 10
    }
    
    return Math.min(score, 100)
  })

  async function login(telegramData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/auth/validate', telegramData)
      user.value = response.data.user
      profile.value = response.data.profile
      preferences.value = response.data.preferences
      
      // Store JWT token (handle both field names for compatibility)
      const token = response.data.token || response.data.access_token
      if (token) {
        localStorage.setItem('jwt_token', token)
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    user.value = null
    profile.value = null
    preferences.value = null
    localStorage.removeItem('jwt_token')
  }

  async function fetchProfile() {
    if (!user.value) return
    
    loading.value = true
    try {
      const response = await api.get(`/profiles/${user.value.id}`)
      profile.value = response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch profile'
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(profileData) {
    if (!user.value) return
    
    loading.value = true
    try {
      const response = await api.put(`/profiles/${user.value.id}`, profileData)
      profile.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPreferences() {
    if (!user.value) return
    
    try {
      const response = await api.get(`/profiles/${user.value.id}/preferences`)
      preferences.value = response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch preferences'
    }
  }

  async function updatePreferences(preferencesData) {
    if (!user.value) return
    
    loading.value = true
    try {
      const response = await api.put(`/profiles/${user.value.id}/preferences`, preferencesData)
      preferences.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update preferences'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    profile,
    preferences,
    loading,
    error,
    isAuthenticated,
    isProfileComplete,
    profileCompletionPercentage,
    login,
    logout,
    fetchProfile,
    updateProfile,
    fetchPreferences,
    updatePreferences
  }
})
