import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const ws = ref(null)
  const isConnected = ref(false)
  const error = ref(null)
  const messageHandlers = ref([])

  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    const token = localStorage.getItem('jwt_token')
    if (!token) {
      error.value = 'No authentication token'
      return
    }

    const wsUrl = `ws://localhost:8080/chat/connect?token=${token}`
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      isConnected.value = true
      error.value = null
      console.log('WebSocket connected')
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        messageHandlers.value.forEach(handler => handler(data))
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.value.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }

    ws.value.onerror = (err) => {
      error.value = 'WebSocket connection error'
      console.error('WebSocket error:', err)
    }
  }

  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
    }
  }

  const sendMessage = (data) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  const onMessage = (handler) => {
    messageHandlers.value.push(handler)
    
    // Return unsubscribe function
    return () => {
      const index = messageHandlers.value.indexOf(handler)
      if (index > -1) {
        messageHandlers.value.splice(index, 1)
      }
    }
  }

  const authenticate = () => {
    const token = localStorage.getItem('jwt_token')
    if (token) {
      sendMessage({
        type: 'authenticate',
        token
      })
    }
  }

  onMounted(() => {
    // Auto-connect if token exists
    const token = localStorage.getItem('jwt_token')
    if (token) {
      connect()
    }
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage,
    onMessage,
    authenticate
  }
}
