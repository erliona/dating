import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'

export const useDiscoveryStore = defineStore('discovery', () => {
  const candidates = ref([])
  const matches = ref([])
  const likes = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentIndex = ref(0)
  const superLikesUsed = ref(0)
  const superLikesLimit = ref(5)

  const { api } = useApi()

  const currentCandidate = computed(() => {
    return candidates.value[currentIndex.value] || null
  })

  const hasMoreCandidates = computed(() => {
    return currentIndex.value < candidates.value.length - 1
  })

  const canSuperLike = computed(() => {
    return superLikesUsed.value < superLikesLimit.value
  })

  async function fetchCandidates() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/discovery/candidates')
      candidates.value = response.data.candidates || []
      currentIndex.value = 0
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch candidates'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function swipe(candidateId, action) {
    if (!candidateId) return
    
    try {
      const response = await api.post('/discovery/swipe', {
        candidate_id: candidateId,
        action: action // 'like', 'pass', 'superlike'
      })
      
      // Update super likes count if superlike was used
      if (action === 'superlike') {
        superLikesUsed.value++
      }
      
      // Move to next candidate
      currentIndex.value++
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Swipe failed'
      throw err
    }
  }

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

  function resetSuperLikes() {
    superLikesUsed.value = 0
  }

  function nextCandidate() {
    if (hasMoreCandidates.value) {
      currentIndex.value++
    }
  }

  function previousCandidate() {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  return {
    candidates,
    matches,
    likes,
    loading,
    error,
    currentIndex,
    superLikesUsed,
    superLikesLimit,
    currentCandidate,
    hasMoreCandidates,
    canSuperLike,
    fetchCandidates,
    swipe,
    fetchMatches,
    fetchLikes,
    resetSuperLikes,
    nextCandidate,
    previousCandidate
  }
})
