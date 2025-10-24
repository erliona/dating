<template>
  <div class="likes-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="likes-header">
      <h1>❤️ Кто лайкнул</h1>
      <button class="btn btn-icon" @click="$router.push('/discovery')">
        🔍
      </button>
    </div>

    <!-- Content -->
    <div class="likes-content">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загружаем лайки...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="likes.length === 0" class="empty-state">
        <div class="empty-icon">💔</div>
        <h3>Пока никто не лайкнул</h3>
        <p>Продолжайте свайпать, чтобы привлечь внимание!</p>
        <button class="btn btn-primary" @click="$router.push('/discovery')">
          Начать поиск
        </button>
      </div>

      <!-- Likes List -->
      <div v-else class="likes-list">
        <div 
          v-for="like in likes" 
          :key="like.id"
          class="like-item"
          :class="{ 'blurred': !like.is_viewed }"
        >
          <div class="like-avatar">
            <img 
              :src="like.is_viewed ? (like.liker_photo || '/default-avatar.png') : '/blurred-avatar.png'" 
              :alt="like.liker_name" 
            />
            <div v-if="like.like_type === 'superlike'" class="superlike-badge">
              ⭐
            </div>
          </div>
          
          <div class="like-info">
            <div class="like-name">
              {{ like.is_viewed ? like.liker_name : '??? ??' }}
            </div>
            <div class="like-age">
              {{ like.is_viewed ? like.liker_age : '??' }} лет
            </div>
            <div class="like-time">
              {{ formatTime(like.created_at) }}
            </div>
          </div>
          
          <div class="like-actions">
            <button 
              v-if="!like.is_viewed"
              class="btn btn-primary btn-small"
              @click="viewLike(like)"
            >
              Посмотреть
            </button>
            <button 
              v-else
              class="btn btn-outline btn-small"
              @click="likeBack(like)"
            >
              Лайкнуть
            </button>
          </div>
        </div>

        <!-- Premium Teaser -->
        <div class="premium-teaser">
          <div class="teaser-content">
            <h3>🔒 Premium</h3>
            <p>Увидеть всех, кто лайкнул вас</p>
            <button class="btn btn-primary" disabled>
              Скоро доступно
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchesStore } from '../stores/matches'
import { useDiscoveryStore } from '../stores/discovery'

const router = useRouter()
const matchesStore = useMatchesStore()
const discoveryStore = useDiscoveryStore()

const loading = ref(false)
const likes = ref([])

const fetchLikes = async () => {
  loading.value = true
  try {
    await matchesStore.fetchLikes()
    likes.value = matchesStore.likes
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const viewLike = async (like) => {
  try {
    // Mark as viewed
    matchesStore.markLikeAsViewed(like.id)
    
    // Update local state
    const likeIndex = likes.value.findIndex(l => l.id === like.id)
    if (likeIndex !== -1) {
      likes.value[likeIndex].is_viewed = true
    }
  } catch (error) {
    // Handle error
  }
}

const likeBack = async (like) => {
  try {
    // Perform like action
    await discoveryStore.swipe(like.liker_id, 'like')
    
    // Show success message or navigate to matches
    router.push('/matches')
  } catch (error) {
    // Handle error
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return 'сейчас'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}м назад`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}ч назад`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}д назад`
  
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  fetchLikes()
})
</script>

<style scoped>
.likes-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.likes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.likes-header h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.likes-content {
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

.likes-list {
  padding: var(--spacing-md);
}

.like-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background-color: white;
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
  box-shadow: var(--shadow-small);
  transition: all var(--transition-fast);
}

.like-item.blurred {
  opacity: 0.7;
}

.like-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: var(--spacing-md);
  flex-shrink: 0;
}

.like-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.superlike-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: var(--accent-color);
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
}

.like-info {
  flex: 1;
  min-width: 0;
}

.like-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.like-age {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.like-time {
  font-size: var(--font-size-xs);
  color: var(--text-light);
}

.like-actions {
  margin-left: var(--spacing-sm);
}

.premium-teaser {
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  text-align: center;
  color: white;
  margin-top: var(--spacing-md);
}

.teaser-content h3 {
  font-size: var(--font-size-md);
  margin-bottom: var(--spacing-sm);
}

.teaser-content p {
  margin-bottom: var(--spacing-md);
  opacity: 0.9;
}

.teaser-content .btn {
  background-color: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
}
</style>
