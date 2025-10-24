<template>
  <div class="welcome-view tg-viewport tg-safe-area">
    <div class="welcome-container">
      <!-- Logo/Header -->
      <div class="welcome-header">
        <h1 class="welcome-title">💕 Dating App</h1>
        <p class="welcome-subtitle">Найди свою любовь</p>
      </div>

      <!-- Features -->
      <div class="welcome-features">
        <div class="feature-item">
          <div class="feature-icon">🎯</div>
          <h3>Умный поиск</h3>
          <p>Алгоритм подберет идеальных кандидатов</p>
        </div>
        <div class="feature-item">
          <div class="feature-icon">💬</div>
          <h3>Безопасный чат</h3>
          <p>Общайтесь только с теми, кто вам понравился</p>
        </div>
        <div class="feature-item">
          <div class="feature-icon">✅</div>
          <h3>Верификация</h3>
          <p>Проверенные профили с синим чекмарком</p>
        </div>
      </div>

      <!-- Login Button -->
      <div class="welcome-actions">
        <button 
          class="btn btn-primary btn-large welcome-btn"
          @click="handleLogin"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>🚀 Начать знакомства</span>
        </button>
        
        
        <p class="welcome-note">
          Вход через Telegram - быстро и безопасно
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useTelegram } from '../composables/useTelegram'

const router = useRouter()
const userStore = useUserStore()
const { getTelegramData, showAlert, initTelegram, isReady } = useTelegram()

const loading = ref(false)

const handleLogin = async () => {
  if (loading.value) return
  
  loading.value = true
  
  try {
    const telegramData = getTelegramData()
    
    // Validate Telegram data
    if (!telegramData?.initData) {
      showAlert('Ошибка: не удалось получить данные Telegram')
      loading.value = false
      return
    }

    // Prepare auth data
    const authData = {
      init_data: telegramData.initData
    }
    
    // Login (sets user, profile, preferences in store)
    await userStore.login(authData)
    
    // Redirect based on profile completion
    if (userStore.isProfileComplete) {
      await router.push('/discovery')
    } else {
      await router.push('/onboarding')
    }
  } catch (error) {
    console.error('Login error:', error)
    showAlert(`Ошибка входа: ${error.response?.data?.error || error.message}`)
    loading.value = false
  }
}

onMounted(() => {
  // Initialize Telegram WebApp
  initTelegram()
})
</script>

<style scoped>
.welcome-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  max-height: 100vh;
  background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
  padding: 10px;
  overflow: hidden;
}

.welcome-container {
  max-width: 100%;
  width: 100%;
  text-align: center;
  color: white;
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
}

.welcome-header {
  margin-bottom: 15px;
  flex-shrink: 0;
}

.welcome-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.welcome-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 0;
}

.welcome-features {
  margin-bottom: 15px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-item {
  margin-bottom: 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.feature-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.feature-item h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.feature-item p {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 0;
}

.welcome-actions {
  margin-bottom: 10px;
  flex-shrink: 0;
}

.welcome-btn {
  width: 100%;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-weight: 600;
  backdrop-filter: blur(10px);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 16px;
}

.welcome-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.welcome-btn:disabled {
  opacity: 0.7;
}

.welcome-note {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 0;
  flex-shrink: 0;
}

.spinner {
  margin-right: 8px;
}
</style>
