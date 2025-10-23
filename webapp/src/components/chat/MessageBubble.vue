<template>
  <div 
    class="message-bubble"
    :class="{ 'own': isOwn, 'system': message.content_type === 'system' }"
  >
    <div v-if="message.content_type === 'system'" class="system-message">
      {{ message.content }}
    </div>
    
    <div v-else class="message-content">
      <div v-if="message.content_type === 'text'" class="text-message">
        {{ message.content }}
      </div>
      
      <div v-else-if="message.content_type === 'image'" class="image-message">
        <img :src="message.content" :alt="'Image from ' + message.sender_name" />
      </div>
      
      <div v-else-if="message.content_type === 'sticker'" class="sticker-message">
        <span class="sticker">{{ message.content }}</span>
      </div>
      
      <div class="message-meta">
        <span class="message-time">{{ formatTime(message.created_at) }}</span>
        <span v-if="isOwn && message.is_read" class="read-status">✓✓</span>
        <span v-else-if="isOwn" class="read-status">✓</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../../stores/user'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const userStore = useUserStore()

const isOwn = computed(() => {
  return props.message.sender_id === userStore.user?.id
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  margin-bottom: var(--spacing-sm);
}

.message-bubble.own {
  justify-content: flex-end;
}

.message-bubble.system {
  justify-content: center;
}

.message-content {
  max-width: 70%;
  position: relative;
}

.message-bubble.own .message-content {
  background-color: var(--primary-color);
  color: white;
  border-radius: 18px 18px 4px 18px;
  padding: var(--spacing-sm) var(--spacing-md);
}

.message-bubble:not(.own) .message-content {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 18px 18px 18px 4px;
  padding: var(--spacing-sm) var(--spacing-md);
}

.system-message {
  background-color: rgba(var(--text-secondary-rgb), 0.1);
  color: var(--text-secondary);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: 12px;
  font-size: var(--font-size-sm);
  text-align: center;
}

.text-message {
  word-wrap: break-word;
  line-height: 1.4;
}

.image-message img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  object-fit: cover;
}

.sticker-message {
  text-align: center;
}

.sticker {
  font-size: 2rem;
  display: inline-block;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xs);
  opacity: 0.7;
}

.message-time {
  font-size: var(--font-size-xs);
}

.read-status {
  font-size: var(--font-size-xs);
  color: var(--primary-color);
}

.message-bubble.own .read-status {
  color: rgba(255, 255, 255, 0.8);
}
</style>
