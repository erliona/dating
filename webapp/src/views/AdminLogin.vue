<template>
  <div class="admin-login tg-viewport tg-safe-area">
    <div class="login-container">
      <div class="login-header">
        <div class="admin-icon">🔧</div>
        <h1>Admin Panel</h1>
        <p>Войдите в панель администратора</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Имя пользователя</label>
          <input 
            id="username"
            v-model="credentials.username" 
            type="text" 
            required
            class="form-input"
            placeholder="admin"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input 
            id="password"
            v-model="credentials.password" 
            type="password" 
            required
            class="form-input"
            placeholder="••••••••"
          />
        </div>

        <button 
          type="submit" 
          class="btn btn-primary btn-lg"
          :disabled="loading"
          :class="{ 'loading': loading }"
        >
          <span v-if="!loading">Войти</span>
          <span v-else>Вход...</span>
        </button>
      </form>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const router = useRouter()
const { post } = useApi()

const credentials = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await post('/admin/auth/login', credentials.value)
    
    // Store admin token
    localStorage.setItem('admin_token', response.data.token)
    
    // Redirect to admin dashboard
    router.push('/admin')
  } catch (err) {
    error.value = err.response?.data?.error || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-lg);
}

.login-container {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-large);
  padding: var(--spacing-xl);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.admin-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.login-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.login-header p {
  color: var(--text-secondary);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-input {
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}

.btn {
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.loading {
  position: relative;
}

.btn.loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: rgba(var(--danger-rgb), 0.1);
  color: var(--danger-color);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  margin-top: var(--spacing-lg);
  text-align: center;
  font-size: var(--font-size-sm);
}
</style>
