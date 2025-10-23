<template>
  <div class="conversation-list">
    <div v-if="loading" class="loading-state">
      <LoadingSpinner size="lg" text="Загрузка чатов..." />
    </div>
    
    <div v-else-if="conversations.length === 0" class="empty-state">
      <div class="empty-icon">💬</div>
      <h3>Пока нет сообщений</h3>
      <p>Начните общение с вашими матчами!</p>
    </div>
    
    <div v-else class="conversations">
      <div 
        v-for="conversation in conversations" 
        :key="conversation.id"
        class="conversation-item"
        :class="{ 'unread': conversation.unread_count > 0 }"
        @click="openConversation(conversation)"
      >
        <div class="conversation-avatar">
          <img 
            :src="getConversationAvatar(conversation)" 
            :alt="getConversationName(conversation)"
          />
          <div v-if="conversation.is_online" class="online-indicator"></div>
        </div>
        
        <div class="conversation-content">
          <div class="conversation-header">
            <h4 class="conversation-name">{{ getConversationName(conversation) }}</h4>
            <span class="conversation-time">{{ formatTime(conversation.last_message_at) }}</span>
          </div>
          
          <div class="conversation-preview">
            <p class="last-message">{{ getLastMessage(conversation) }}</p>
            <div v-if="conversation.unread_count > 0" class="unread-badge">
              {{ conversation.unread_count }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../../stores/chat'
import LoadingSpinner from '../common/LoadingSpinner.vue'

const router = useRouter()
const chatStore = useChatStore()

const loading = ref(false)
const conversations = ref([])

const fetchConversations = async () => {
  loading.value = true
  try {
    conversations.value = await chatStore.fetchConversations()
  } catch (error) {
    console.error('Failed to fetch conversations:', error)
  } finally {
    loading.value = false
  }
}

const openConversation = (conversation) => {
  router.push(`/chat/${conversation.id}`)
}

const getConversationAvatar = (conversation) => {
  // This would need to be implemented with actual user data
  return conversation.avatar_url || '/default-avatar.png'
}

const getConversationName = (conversation) => {
  // This would need to be implemented with actual user data
  return conversation.name || 'User'
}

const getLastMessage = (conversation) => {
  if (!conversation.last_message) return 'Нет сообщений'
  
  const message = conversation.last_message
  if (message.content_type === 'text') {
    return message.content
  } else if (message.content_type === 'image') {
    return '📷 Фото'
  } else if (message.content_type === 'sticker') {
    return '😊 Стикер'
  }
  return 'Сообщение'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffInHours = (now - date) / (1000 * 60 * 60)
  
  if (diffInHours < 1) {
    return 'сейчас'
  } else if (diffInHours < 24) {
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (diffInHours < 48) {
    return 'вчера'
  } else {
    return date.toLocaleDateString('ru-RU', { 
      day: 'numeric', 
      month: 'short' 
    })
  }
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.conversation-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: var(--spacing-xl);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-lg);
}

.empty-state h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.empty-state p {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0;
}

.conversations {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.conversation-item:hover {
  background-color: var(--bg-secondary);
}

.conversation-item.unread {
  background-color: rgba(var(--primary-rgb), 0.05);
}

.conversation-avatar {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.conversation-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.online-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  background-color: var(--success-color);
  border: 2px solid white;
  border-radius: 50%;
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.conversation-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
  margin-left: var(--spacing-sm);
}

.conversation-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
}

.last-message {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.unread-badge {
  background-color: var(--primary-color);
  color: white;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
