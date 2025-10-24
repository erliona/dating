<template>
  <div class="match-popup-overlay" @click="close">
    <div class="match-popup" @click.stop>
      <!-- Match Animation -->
      <div class="match-animation">
        <div class="hearts">💕💕💕</div>
        <h2>Это Match!</h2>
        <p>Вы понравились друг другу!</p>
      </div>

      <!-- Photos -->
      <div class="match-photos">
        <div class="photo-container">
          <img :src="userPhoto" :alt="'Your photo'" class="match-photo" />
        </div>
        <div class="heart-between">❤️</div>
        <div class="photo-container">
          <img :src="matchPhoto" :alt="'Match photo'" class="match-photo" />
        </div>
      </div>

      <!-- Match Info -->
      <div class="match-info">
        <h3>{{ match.name }}</h3>
        <p>Теперь вы можете начать общение!</p>
      </div>

      <!-- Actions -->
      <div class="match-actions">
        <button class="btn btn-outline" @click="close">
          Продолжить поиск
        </button>
        <button class="btn btn-primary" @click="startChat">
          Написать сообщение
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'

const props = defineProps({
  match: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'chat'])

const router = useRouter()
const userStore = useUserStore()

const userPhoto = computed(() => {
  return userStore.profile?.photos?.[0]?.url || '/default-avatar.png'
})

const matchPhoto = computed(() => {
  return props.match.photos?.[0]?.url || '/default-avatar.png'
})

const close = () => {
  emit('close')
}

const startChat = () => {
  emit('chat', props.match.conversation_id)
  close()
}
</script>

<style scoped>
.match-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-md);
}

.match-popup {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  text-align: center;
  max-width: 400px;
  width: 100%;
  box-shadow: var(--shadow-large);
  animation: popup-appear 0.3s ease-out;
}

@keyframes popup-appear {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.match-animation {
  margin-bottom: var(--spacing-md);
}

.hearts {
  font-size: var(--font-size-xxl);
  margin-bottom: var(--spacing-md);
  animation: hearts-bounce 1s ease-in-out infinite;
}

@keyframes hearts-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.match-animation h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--primary-color);
  margin-bottom: var(--spacing-sm);
}

.match-animation p {
  color: var(--text-secondary);
  margin-bottom: 0;
}

.match-photos {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.photo-container {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid var(--primary-color);
}

.match-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.heart-between {
  font-size: var(--font-size-lg);
  animation: heart-pulse 1s ease-in-out infinite;
}

@keyframes heart-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.match-info {
  margin-bottom: var(--spacing-md);
}

.match-info h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.match-info p {
  color: var(--text-secondary);
  margin-bottom: 0;
}

.match-actions {
  display: flex;
  gap: var(--spacing-md);
}

.match-actions .btn {
  flex: 1;
}
</style>
