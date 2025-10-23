import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const messages = ref({}) // conversationId -> messages[]
  const activeConversation = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const typingUsers = ref({}) // conversationId -> userId[]

  const { api } = useApi()
  const { connect, disconnect, sendMessage, onMessage, isConnected } = useWebSocket()

  const activeMessages = computed(() => {
    if (!activeConversation.value) return []
    return messages.value[activeConversation.value.id] || []
  })

  const unreadCount = computed(() => {
    return conversations.value.reduce((total, conv) => {
      return total + (conv.unread_count || 0)
    }, 0)
  })

  async function fetchConversations() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/chat/conversations')
      conversations.value = response.data.conversations || []
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch conversations'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMessages(conversationId, limit = 50, offset = 0) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get(`/chat/conversations/${conversationId}/messages`, {
        params: { limit, offset }
      })
      
      if (!messages.value[conversationId]) {
        messages.value[conversationId] = []
      }
      
      if (offset === 0) {
        messages.value[conversationId] = response.data.messages || []
      } else {
        messages.value[conversationId].push(...(response.data.messages || []))
      }
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch messages'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function sendMessageToConversation(conversationId, content, contentType = 'text') {
    try {
      const response = await api.post('/chat/messages', {
        conversation_id: conversationId,
        content,
        content_type: contentType
      })
      
      // Add message to local state
      if (!messages.value[conversationId]) {
        messages.value[conversationId] = []
      }
      messages.value[conversationId].unshift(response.data.message)
      
      // Send via WebSocket for real-time delivery
      sendMessage({
        type: 'send_message',
        conversation_id: conversationId,
        content,
        content_type: contentType
      })
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to send message'
      throw err
    }
  }

  async function markMessageAsRead(messageId) {
    try {
      await api.put(`/chat/messages/${messageId}/read`)
      
      // Update local state
      Object.keys(messages.value).forEach(convId => {
        const message = messages.value[convId].find(msg => msg.id === messageId)
        if (message) {
          message.is_read = true
        }
      })
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to mark message as read'
    }
  }

  async function blockConversation(conversationId) {
    try {
      await api.post(`/chat/conversations/${conversationId}/block`)
      
      // Update local state
      const conversation = conversations.value.find(conv => conv.id === conversationId)
      if (conversation) {
        conversation.is_blocked = true
      }
      
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to block conversation'
      throw err
    }
  }

  async function reportConversation(conversationId, reportType, reason) {
    try {
      await api.post(`/chat/conversations/${conversationId}/report`, {
        report_type: reportType,
        reason
      })
      
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to report conversation'
      throw err
    }
  }

  function setActiveConversation(conversation) {
    activeConversation.value = conversation
  }

  function addMessage(conversationId, message) {
    if (!messages.value[conversationId]) {
      messages.value[conversationId] = []
    }
    
    // Check if message already exists
    const exists = messages.value[conversationId].find(msg => msg.id === message.id)
    if (!exists) {
      messages.value[conversationId].unshift(message)
    }
  }

  function updateTyping(conversationId, userId, isTyping) {
    if (!typingUsers.value[conversationId]) {
      typingUsers.value[conversationId] = []
    }
    
    if (isTyping) {
      if (!typingUsers.value[conversationId].includes(userId)) {
        typingUsers.value[conversationId].push(userId)
      }
    } else {
      typingUsers.value[conversationId] = typingUsers.value[conversationId].filter(id => id !== userId)
    }
  }

  function connectWebSocket() {
    connect()
    
    // Listen for incoming messages
    onMessage((data) => {
      if (data.type === 'message') {
        addMessage(data.conversation_id, data)
      } else if (data.type === 'typing') {
        updateTyping(data.conversation_id, data.user_id, data.is_typing)
      }
    })
  }

  function disconnectWebSocket() {
    disconnect()
  }

  return {
    conversations,
    messages,
    activeConversation,
    loading,
    error,
    typingUsers,
    activeMessages,
    unreadCount,
    fetchConversations,
    fetchMessages,
    sendMessageToConversation,
    markMessageAsRead,
    blockConversation,
    reportConversation,
    setActiveConversation,
    addMessage,
    updateTyping,
    connectWebSocket,
    disconnectWebSocket
  }
})
