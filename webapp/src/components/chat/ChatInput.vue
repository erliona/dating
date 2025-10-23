<template>
  <div class="chat-input">
    <div class="input-container">
      <button 
        class="attach-button"
        @click="showAttachmentMenu = !showAttachmentMenu"
        :disabled="disabled"
      >
        📎
      </button>
      
      <div class="input-wrapper">
        <textarea
          v-model="message"
          placeholder="Напишите сообщение..."
          rows="1"
          class="message-input"
          @keydown="handleKeyDown"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
          :disabled="disabled"
          ref="textareaRef"
        ></textarea>
        
        <div v-if="showAttachmentMenu" class="attachment-menu">
          <button class="attachment-option" @click="selectImage">
            📷 Фото
          </button>
          <button class="attachment-option" @click="selectSticker">
            😊 Стикер
          </button>
        </div>
      </div>
      
      <button 
        class="send-button"
        @click="sendMessage"
        :disabled="!canSend"
      >
        {{ sending ? '⏳' : '➤' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: 'Напишите сообщение...'
  }
})

const emit = defineEmits(['send', 'typing-start', 'typing-stop'])

const message = ref('')
const sending = ref(false)
const showAttachmentMenu = ref(false)
const isTyping = ref(false)
const typingTimeout = ref(null)
const textareaRef = ref(null)

const canSend = computed(() => {
  return message.value.trim().length > 0 && !sending.value && !props.disabled
})

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const handleInput = () => {
  adjustTextareaHeight()
  handleTyping()
}

const handleFocus = () => {
  handleTyping()
}

const handleBlur = () => {
  handleTypingStop()
}

const adjustTextareaHeight = () => {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
    }
  })
}

const handleTyping = () => {
  if (!isTyping.value) {
    isTyping.value = true
    emit('typing-start')
  }
  
  clearTimeout(typingTimeout.value)
  typingTimeout.value = setTimeout(() => {
    handleTypingStop()
  }, 1000)
}

const handleTypingStop = () => {
  if (isTyping.value) {
    isTyping.value = false
    emit('typing-stop')
  }
}

const sendMessage = async () => {
  if (!canSend.value) return
  
  const messageText = message.value.trim()
  if (!messageText) return
  
  sending.value = true
  
  try {
    emit('send', {
      content: messageText,
      content_type: 'text'
    })
    message.value = ''
    adjustTextareaHeight()
  } catch (error) {
    console.error('Failed to send message:', error)
  } finally {
    sending.value = false
  }
}

const selectImage = () => {
  // TODO: Implement image selection
  showAttachmentMenu.value = false
}

const selectSticker = () => {
  // TODO: Implement sticker selection
  showAttachmentMenu.value = false
}

// Watch for external changes to message
watch(() => props.disabled, (newDisabled) => {
  if (newDisabled) {
    handleTypingStop()
  }
})
</script>

<style scoped>
.chat-input {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
  position: relative;
}

.attach-button {
  background: none;
  border: none;
  font-size: var(--font-size-lg);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: 50%;
  transition: background-color 0.2s ease;
  flex-shrink: 0;
}

.attach-button:hover:not(:disabled) {
  background-color: var(--bg-primary);
}

.attach-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.message-input {
  width: 100%;
  min-height: 40px;
  max-height: 120px;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: var(--font-size-md);
  font-family: inherit;
  resize: none;
  background-color: white;
  transition: border-color 0.2s ease;
}

.message-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.message-input:disabled {
  background-color: var(--bg-secondary);
  cursor: not-allowed;
}

.attachment-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-medium);
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  z-index: 10;
}

.attachment-option {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  border-radius: var(--border-radius);
  transition: background-color 0.2s ease;
}

.attachment-option:hover {
  background-color: var(--bg-secondary);
}

.send-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button:hover:not(:disabled) {
  background-color: var(--primary-dark);
  transform: scale(1.05);
}

.send-button:disabled {
  background-color: var(--border-color);
  cursor: not-allowed;
  transform: none;
}
</style>
