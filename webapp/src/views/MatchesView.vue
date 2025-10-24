<template>
  <div class="matches-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="matches-header">
      <h1>💬 Matches</h1>
      <button class="btn btn-icon" @click="$router.push('/discovery')">
        🔍
      </button>
    </div>

    <!-- Content -->
    <div class="matches-content">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загружаем matches...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="matches.length === 0" class="empty-state">
        <div class="empty-icon">💔</div>
        <h3>Пока нет matches</h3>
        <p>Начните свайпать, чтобы найти свою любовь!</p>
        <button class="btn btn-primary" @click="$router.push('/discovery')">
          Начать поиск
        </button>
      </div>

      <!-- Matches List -->
      <div v-else class="matches-list">
        <div 
          v-for="match in matches" 
          :key="match.id"
          class="match-item"
          @click="openConversation(match)"
        >
          <div class="match-avatar">
            <img :src="match.photos?.[0]?.url || '/default-avatar.png'" :alt="match.name" />
            <div v-if="match.unread_count > 0" class="unread-badge">
              {{ match.unread_count }}
            </div>
          </div>
          
          <div class="match-info">
            <div class="match-name">
              {{ match.name }}
              <span v-if="match.is_verified" class="verified-badge">✅</span>
            </div>
            <div class="match-preview">
              {{ match.last_message || 'Начните общение!' }}
            </div>
            <div class="match-time">
              {{ formatTime(match.last_message_at) }}
            </div>
          </div>
          
          <div class="match-arrow">→</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchesStore } from '../stores/matches'

const router = useRouter()
const matchesStore = useMatchesStore()

const loading = ref(false)
const matches = ref([])

const fetchMatches = async () => {
  loading.value = true
  try {
    await matchesStore.fetchMatches()
    matches.value = matchesStore.matches
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const openConversation = (match) => {
  router.push(`/chat/${match.conversation_id}`)
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return 'сейчас'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}м`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}ч`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}д`
  
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  fetchMatches()
})
</script>

<style scoped>
.matches-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.matches-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.matches-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.matches-content {
  flex: 1;
  overflow-y: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
}

.loading-state .spinner {
  margin-bottom: var(--spacing-md);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: var(--font-size-xxxl);
  margin-bottom: var(--spacing-md);
}

.empty-state h3 {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.empty-state p {
  margin-bottom: var(--spacing-lg);
}

.matches-list {
  padding: var(--spacing-md);
}

.match-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background-color: white;
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
  box-shadow: var(--shadow-small);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.match-item:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-medium);
}

.match-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: var(--spacing-md);
  flex-shrink: 0;
}

.match-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.unread-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.match-info {
  flex: 1;
  min-width: 0;
}

.match-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.verified-badge {
  font-size: var(--font-size-sm);
}

.match-preview {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-time {
  font-size: var(--font-size-xs);
  color: var(--text-light);
}

.match-arrow {
  font-size: var(--font-size-lg);
  color: var(--text-light);
  margin-left: var(--spacing-sm);
}
</style>
