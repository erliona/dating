import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'

export const useMatchesStore = defineStore('matches', () => {
  const matches = ref([])
  const likes = ref([])
  const loading = ref(false)
  const error = ref(null)

  const { api } = useApi()

  const totalMatches = computed(() => matches.value.length)
  const totalLikes = computed(() => likes.value.length)
  const unviewedLikes = computed(() => likes.value.filter(like => !like.is_viewed).length)

  async function fetchMatches() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/discovery/matches')
      matches.value = response.data.matches || []
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch matches'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchLikes() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/discovery/likes')
      likes.value = response.data.likes || []
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch likes'
      throw err
    } finally {
      loading.value = false
    }
  }

  function addMatch(match) {
    // Check if match already exists
    const exists = matches.value.find(m => m.id === match.id)
    if (!exists) {
      matches.value.unshift(match)
    }
  }

  function addLike(like) {
    // Check if like already exists
    const exists = likes.value.find(l => l.id === like.id)
    if (!exists) {
      likes.value.unshift(like)
    }
  }

  function markLikeAsViewed(likeId) {
    const like = likes.value.find(l => l.id === likeId)
    if (like) {
      like.is_viewed = true
    }
  }

  return {
    matches,
    likes,
    loading,
    error,
    totalMatches,
    totalLikes,
    unviewedLikes,
    fetchMatches,
    fetchLikes,
    addMatch,
    addLike,
    markLikeAsViewed
  }
})
