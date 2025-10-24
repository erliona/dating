<template>
  <div class="conversation-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="conversation-header">
      <button class="btn btn-icon" @click="$router.back()">
        ←
      </button>
      <div class="header-info">
        <div class="header-avatar">
          <img :src="getConversationAvatar()" :alt="getConversationName()" />
        </div>
        <div class="header-details">
          <h3>{{ getConversationName() }}</h3>
          <p v-if="isTyping" class="typing-indicator">печатает...</p>
          <p v-else-if="isOnline" class="online-status">в сети</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-icon" @click="showReportModal = true">
          ⚠️
        </button>
        <button class="btn btn-icon" @click="showBlockModal = true">
          🚫
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
      </div>
      
      <div v-else-if="messages.length === 0" class="empty-state">
        <p>Начните общение!</p>
      </div>
      
      <div v-else class="messages-list">
        <div 
          v-for="message in messages" 
          :key="message.id"
          class="message-item"
          :class="{ 'own': message.sender_id === userStore.user?.id }"
        >
          <div class="message-bubble">
            <div class="message-content">
              {{ message.content }}
            </div>
            <div class="message-time">
              {{ formatMessageTime(message.created_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Typing Indicator -->
    <div v-if="isTyping" class="typing-indicator">
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <!-- Message Input -->
    <div class="message-input-container">
      <div class="message-input">
        <input
          v-model="newMessage"
          type="text"
          placeholder="Напишите сообщение..."
          @keyup.enter="sendMessage"
          @input="handleTyping"
        />
        <button 
          class="btn btn-primary btn-icon"
          @click="sendMessage"
          :disabled="!newMessage.trim()"
        >
          ➤
        </button>
      </div>
    </div>

    <!-- Report Modal -->
    <div v-if="showReportModal" class="modal-overlay" @click="showReportModal = false">
      <div class="modal" @click.stop>
        <h3>Пожаловаться на пользователя</h3>
        <div class="report-options">
          <label v-for="option in reportOptions" :key="option.value" class="report-option">
            <input
              v-model="selectedReportType"
              type="radio"
              :value="option.value"
              name="report"
            />
            <span>{{ option.label }}</span>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showReportModal = false">
            Отмена
          </button>
          <button class="btn btn-primary" @click="submitReport">
            Пожаловаться
          </button>
        </div>
      </div>
    </div>

    <!-- Block Modal -->
    <div v-if="showBlockModal" class="modal-overlay" @click="showBlockModal = false">
      <div class="modal" @click.stop>
        <h3>Заблокировать пользователя</h3>
        <p>Вы больше не будете видеть сообщения от этого пользователя.</p>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showBlockModal = false">
            Отмена
          </button>
          <button class="btn btn-primary" @click="blockUser">
            Заблокировать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import { useTelegram } from '../composables/useTelegram'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()
const { showAlert } = useTelegram()

const conversationId = computed(() => parseInt(route.params.conversationId))
const loading = ref(false)
const newMessage = ref('')
const isTyping = ref(false)
const isOnline = ref(false)
const showReportModal = ref(false)
const showBlockModal = ref(false)
const selectedReportType = ref('')
const messagesContainer = ref(null)

const messages = computed(() => chatStore.activeMessages)

const reportOptions = [
  { value: 'spam', label: 'Спам' },
  { value: 'inappropriate_content', label: 'Неподходящий контент' },
  { value: 'harassment', label: 'Домогательства' },
  { value: 'fake_profile', label: 'Фейковый профиль' },
  { value: 'other', label: 'Другое' }
]

const fetchMessages = async () => {
  loading.value = true
  try {
    await chatStore.fetchMessages(conversationId.value)
    scrollToBottom()
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim()) return

  try {
    await chatStore.sendMessageToConversation(
      conversationId.value,
      newMessage.value.trim()
    )
    newMessage.value = ''
    scrollToBottom()
  } catch (error) {
    // Handle error
    showAlert('Не удалось отправить сообщение')
  }
}

const handleTyping = () => {
  // TODO: Implement typing indicator
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const getConversationName = () => {
  // This would need to be implemented with actual user data
  return 'User Name'
}

const getConversationAvatar = () => {
  // This would need to be implemented with actual user photos
  return '/default-avatar.png'
}

const formatMessageTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const submitReport = async () => {
  if (!selectedReportType.value) return

  try {
    await chatStore.reportConversation(
      conversationId.value,
      selectedReportType.value,
      'Report from conversation'
    )
    showReportModal.value = false
    showAlert('Жалоба отправлена')
  } catch (error) {
    // Handle error
    showAlert('Не удалось отправить жалобу')
  }
}

const blockUser = async () => {
  try {
    await chatStore.blockConversation(conversationId.value)
    showBlockModal.value = false
    showAlert('Пользователь заблокирован')
    router.back()
  } catch (error) {
    // Handle error
    showAlert('Не удалось заблокировать пользователя')
  }
}

onMounted(() => {
  fetchMessages()
  chatStore.connectWebSocket()
})

onUnmounted(() => {
  chatStore.disconnectWebSocket()
})
</script>

<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.conversation-header {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.header-info {
  display: flex;
  align-items: center;
  flex: 1;
  margin: 0 var(--spacing-md);
}

.header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: var(--spacing-md);
}

.header-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-details h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.header-details p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.typing-indicator {
  color: var(--primary-color);
}

.online-status {
  color: var(--success-color);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
  color: var(--text-secondary);
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.message-item {
  display: flex;
  justify-content: flex-start;
}

.message-item.own {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 70%;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  background-color: var(--bg-secondary);
  position: relative;
}

.message-item.own .message-bubble {
  background-color: var(--primary-color);
  color: white;
}

.message-content {
  margin-bottom: var(--spacing-xs);
  word-wrap: break-word;
}

.message-time {
  font-size: var(--font-size-xs);
  opacity: 0.7;
  text-align: right;
}

.typing-indicator {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin: 0 var(--spacing-md) var(--spacing-sm);
}

.typing-dots {
  display: flex;
  gap: var(--spacing-xs);
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-input-container {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.message-input {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.message-input input {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  background-color: white;
}

.message-input input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.modal {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  max-width: 400px;
  width: 100%;
  box-shadow: var(--shadow-large);
}

.modal h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-lg);
  color: var(--text-primary);
}

.report-options {
  margin-bottom: var(--spacing-lg);
}

.report-option {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) 0;
  cursor: pointer;
}

.report-option input[type="radio"] {
  margin-right: var(--spacing-sm);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.modal-actions .btn {
  min-width: 100px;
}
</style>
