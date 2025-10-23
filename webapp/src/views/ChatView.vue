<template>
  <div class="chat-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="chat-header">
      <h1>💬 Чаты</h1>
      <button class="btn btn-icon" @click="$router.push('/discovery')">
        🔍
      </button>
    </div>

    <!-- Content -->
    <div class="chat-content">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загружаем чаты...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="conversations.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <h3>Пока нет чатов</h3>
        <p>Начните общение с вашими matches!</p>
        <button class="btn btn-primary" @click="$router.push('/discovery')">
          Найти matches
        </button>
      </div>

      <!-- Conversations List -->
      <div v-else class="conversations-list">
        <div 
          v-for="conversation in conversations" 
          :key="conversation.id"
          class="conversation-item"
          @click="openConversation(conversation)"
        >
          <div class="conversation-avatar">
            <img :src="getConversationAvatar(conversation)" :alt="getConversationName(conversation)" />
            <div v-if="conversation.unread_count > 0" class="unread-badge">
              {{ conversation.unread_count }}
            </div>
          </div>
          
          <div class="conversation-info">
            <div class="conversation-name">
              {{ getConversationName(conversation) }}
              <span v-if="conversation.is_verified" class="verified-badge">✅</span>
            </div>
            <div class="conversation-preview">
              {{ getLastMessagePreview(conversation) }}
            </div>
            <div class="conversation-time">
              {{ formatTime(conversation.last_message_at) }}
            </div>
          </div>
          
          <div class="conversation-arrow">→</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const loading = ref(false)
const conversations = ref([])

const fetchConversations = async () => {
  loading.value = true
  try {
    await chatStore.fetchConversations()
    conversations.value = chatStore.conversations
  } catch (error) {
    console.error('Failed to fetch conversations:', error)
  } finally {
    loading.value = false
  }
}

const openConversation = (conversation) => {
  router.push(`/chat/${conversation.id}`)
}

const getConversationName = (conversation) => {
  // This would need to be implemented with actual user data
  return `User ${conversation.user1_id === userStore.user?.id ? conversation.user2_id : conversation.user1_id}`
}

const getConversationAvatar = (conversation) => {
  // This would need to be implemented with actual user photos
  return '/default-avatar.png'
}

const getLastMessagePreview = (conversation) => {
  // This would need to be implemented with actual message data
  return 'Начните общение!'
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
  fetchConversations()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.chat-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.chat-content {
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

.conversations-list {
  padding: var(--spacing-md);
}

.conversation-item {
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

.conversation-item:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-medium);
}

.conversation-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: var(--spacing-md);
  flex-shrink: 0;
}

.conversation-avatar img {
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

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-name {
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

.conversation-preview {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: var(--font-size-xs);
  color: var(--text-light);
}

.conversation-arrow {
  font-size: var(--font-size-lg);
  color: var(--text-light);
  margin-left: var(--spacing-sm);
}
</style>
