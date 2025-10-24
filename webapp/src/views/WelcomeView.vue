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
          @click.prevent="handleLogin"
          onclick="console.log('Inline click on main button!'); window.handleLogin && window.handleLogin();"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>🚀 Начать знакомства</span>
        </button>
        
        <!-- Test button -->
        <button 
          class="btn btn-secondary btn-large"
          @click="testClick"
          style="margin-top: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: white;"
        >
          🧪 Тест кнопки
        </button>
        
        <!-- Simple test button -->
        <button 
          onclick="alert('Inline click works!')"
          style="margin-top: 10px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 10px; border-radius: 5px;"
        >
          🔥 Inline Test
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

const testClick = () => {
  console.log('TEST BUTTON CLICKED!')
  alert('Тест кнопка работает!')
}

onMounted(() => {
  console.log('WelcomeView mounted')
  console.log('Telegram WebApp available:', !!window.Telegram?.WebApp)
  console.log('isReady:', isReady.value)
  
  // Force initialization
  initTelegram()
  
  // Check again after initialization
  setTimeout(() => {
    console.log('After init - isReady:', isReady.value)
    console.log('Telegram data after init:', getTelegramData())
  }, 100)
  
  // Add simple click test
  const button = document.querySelector('.welcome-btn')
  if (button) {
    button.addEventListener('click', (e) => {
      console.log('Button clicked directly!', e)
    })
  }
  
  // Make handleLogin available globally for inline calls
  window.handleLogin = handleLogin
})

const handleLogin = async () => {
  console.log('handleLogin called!')
  console.log('loading before:', loading.value)
  
  loading.value = true
  console.log('loading after:', loading.value)
  
  try {
    const telegramData = getTelegramData()
    console.log('Telegram data:', telegramData)
    
    if (!telegramData?.user) {
      console.error('No user data in telegramData:', telegramData)
      console.log('Telegram WebApp not properly initialized. This might be a development environment.')
      
      // For development/testing, create mock data
      if (telegramData.initData === '') {
        console.log('Using mock data for development')
        const mockAuthData = {
          init_data: 'user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22en%22%7D&chat_instance=-123456789&chat_type=sender&auth_date=' + Math.floor(Date.now() / 1000) + '&hash=mock_hash',
          bot_token: '8302871321:AAGDRnSDYdYHeEOqtEoKZVYLCbBlI2GBYMM'
        }
        
        console.log('Mock auth data:', mockAuthData)
        console.log('Sending mock login request...')
        
        try {
          await userStore.login(mockAuthData)
          
          // Redirect based on profile completion
          if (userStore.isProfileComplete) {
            router.push('/discovery')
          } else {
            router.push('/onboarding')
          }
        } catch (error) {
          console.error('Mock login error:', error)
          alert(`Ошибка входа: ${error.response?.data?.error || error.message}`)
        } finally {
          loading.value = false
        }
        return
      }
      
      showAlert('Ошибка: не удалось получить данные Telegram')
      return
    }

    // Prepare data for authentication
    const authData = {
      init_data: telegramData.raw_data || telegramData.initData,
      bot_token: telegramData.bot_token || '8302871321:AAGDRnSDYdYHeEOqtEoKZVYLCbBlI2GBYMM'
    }
    
    console.log('Auth data:', authData)
    console.log('Sending login request...')

    await userStore.login(authData)
    
    // Redirect based on profile completion
    if (userStore.isProfileComplete) {
      router.push('/discovery')
    } else {
      router.push('/onboarding')
    }
    
  } catch (error) {
    console.error('Login error:', error)
    console.error('Error details:', error.response?.data || error.message)
    showAlert(`Ошибка входа: ${error.response?.data?.error || error.message}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.welcome-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
  padding: var(--spacing-lg);
}

.welcome-container {
  max-width: 400px;
  width: 100%;
  text-align: center;
  color: white;
}

.welcome-header {
  margin-bottom: var(--spacing-xxl);
}

.welcome-title {
  font-size: var(--font-size-xxxl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--spacing-sm);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.welcome-subtitle {
  font-size: var(--font-size-lg);
  opacity: 0.9;
  margin-bottom: 0;
}

.welcome-features {
  margin-bottom: var(--spacing-xxl);
}

.feature-item {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--border-radius);
  backdrop-filter: blur(10px);
}

.feature-icon {
  font-size: var(--font-size-xxxl);
  margin-bottom: var(--spacing-md);
}

.feature-item h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-sm);
}

.feature-item p {
  font-size: var(--font-size-sm);
  opacity: 0.9;
  margin-bottom: 0;
}

.welcome-actions {
  margin-bottom: var(--spacing-lg);
}

.welcome-btn {
  width: 100%;
  margin-bottom: var(--spacing-md);
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-weight: var(--font-weight-semibold);
  backdrop-filter: blur(10px);
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
  font-size: var(--font-size-sm);
  opacity: 0.8;
  margin-bottom: 0;
}

.spinner {
  margin-right: var(--spacing-sm);
}
</style>
