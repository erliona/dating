<template>
  <div v-if="isTyping" class="typing-indicator">
    <div class="typing-content">
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <span class="typing-text">{{ typingText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isTyping: {
    type: Boolean,
    default: false
  },
  userName: {
    type: String,
    default: 'Пользователь'
  }
})

const typingText = computed(() => {
  return `${props.userName} печатает...`
})
</script>

<style scoped>
.typing-indicator {
  display: flex;
  justify-content: flex-start;
  margin-bottom: var(--spacing-sm);
}

.typing-content {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: 18px 18px 18px 4px;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  max-width: 200px;
}

.typing-dots {
  display: flex;
  gap: 3px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.typing-text {
  font-size: var(--font-size-sm);
  font-style: italic;
}
</style>
