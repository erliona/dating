<template>
  <div class="discovery-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="discovery-header">
      <h1>💕 Discovery</h1>
      <div class="header-actions">
        <button class="btn btn-icon" @click="$router.push('/matches')">
          💬
        </button>
        <button class="btn btn-icon" @click="$router.push('/likes')">
          ❤️
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="discovery-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Ищем кандидатов...</p>
      </div>

      <!-- No Candidates -->
      <div v-else-if="!hasMoreCandidates" class="empty-state">
        <div class="empty-icon">😔</div>
        <h3>Пока что никого нет</h3>
        <p>Попробуйте расширить поиск в настройках</p>
        <button class="btn btn-primary" @click="fetchCandidates">
          Обновить
        </button>
      </div>

      <!-- Swipe Cards -->
      <div v-else class="swipe-container">
        <SwipeCard
          v-if="currentCandidate"
          :candidate="currentCandidate"
          @swipe="handleSwipe"
          @superlike="handleSuperLike"
          @block="handleBlock"
          @report="handleReport"
        />
      </div>
    </div>

    <!-- Action Buttons -->
    <div v-if="currentCandidate && !loading" class="action-buttons">
      <button 
        class="btn btn-icon action-btn pass-btn"
        @click="handlePass"
      >
        ✖️
      </button>
      
      <button 
        class="btn btn-icon action-btn superlike-btn"
        @click="handleSuperLike"
        :disabled="!canSuperLike"
      >
        ⭐
      </button>
      
      <button 
        class="btn btn-icon action-btn like-btn"
        @click="handleLike"
      >
        ❤️
      </button>
    </div>

    <!-- Super Like Counter -->
    <div v-if="!canSuperLike" class="superlike-info">
      Super Like: {{ superLikesUsed }}/{{ superLikesLimit }}
    </div>

    <!-- Match Popup -->
    <MatchPopup
      v-if="showMatchPopup"
      :match="lastMatch"
      @close="showMatchPopup = false"
      @chat="goToChat"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDiscoveryStore } from '../stores/discovery'
import { useMatchesStore } from '../stores/matches'
import { useTelegram } from '../composables/useTelegram'
import SwipeCard from '../components/discovery/SwipeCard.vue'
import MatchPopup from '../components/discovery/MatchPopup.vue'

const router = useRouter()
const discoveryStore = useDiscoveryStore()
const matchesStore = useMatchesStore()
const { hapticFeedback } = useTelegram()

const loading = ref(false)
const showMatchPopup = ref(false)
const lastMatch = ref(null)

const {
  candidates,
  currentCandidate,
  hasMoreCandidates,
  canSuperLike,
  superLikesUsed,
  superLikesLimit,
  fetchCandidates,
  swipe
} = discoveryStore

const { blockUser, reportUser } = useApi()

const handleSwipe = async (action) => {
  if (!currentCandidate.value) return

  try {
    hapticFeedback('impact')
    
    const result = await swipe(currentCandidate.value.id, action)
    
    if (result.is_match) {
      lastMatch.value = result.match
      showMatchPopup.value = true
      hapticFeedback('notification')
      
      // Add to matches store
      matchesStore.addMatch(result.match)
    }
    
  } catch (error) {
    // Handle error
  }
}

const handleLike = () => {
  handleSwipe('like')
}

const handlePass = () => {
  handleSwipe('pass')
}

const handleSuperLike = () => {
  if (canSuperLike.value) {
    handleSwipe('superlike')
  }
}

const handleBlock = async (userId) => {
  try {
    await blockUser(userId)
    // Remove from candidates and load next
    await loadNextCandidate()
  } catch (error) {
    console.error('Error blocking user:', error)
  }
}

const handleReport = async (reportData) => {
  try {
    await reportUser(reportData.userId, reportData.reason)
    // Remove from candidates and load next
    await loadNextCandidate()
  } catch (error) {
    console.error('Error reporting user:', error)
  }
}

const goToChat = (conversationId) => {
  showMatchPopup.value = false
  router.push(`/chat/${conversationId}`)
}

onMounted(async () => {
  loading.value = true
  try {
    await fetchCandidates()
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.discovery-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.discovery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.discovery-header h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.discovery-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
  overflow: hidden;
}

.loading-state {
  text-align: center;
  color: var(--text-secondary);
}

.loading-state .spinner {
  margin: 0 auto var(--spacing-md);
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: var(--font-size-xxl);
  margin-bottom: var(--spacing-md);
}

.empty-state h3 {
  font-size: var(--font-size-md);
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.empty-state p {
  margin-bottom: var(--spacing-md);
}

.swipe-container {
  width: 100%;
  max-width: 400px;
  height: 600px;
  position: relative;
}

.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.action-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  font-size: var(--font-size-lg);
  border: none;
  box-shadow: var(--shadow-medium);
  transition: all var(--transition-fast);
}

.action-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.pass-btn {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.like-btn {
  background-color: var(--primary-color);
  color: white;
}

.superlike-btn {
  background-color: var(--accent-color);
  color: white;
}

.superlike-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.superlike-info {
  text-align: center;
  padding: var(--spacing-sm);
  background-color: var(--warning-color);
  color: white;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}
</style>
