<template>
  <div class="verification-flow">
    <div v-if="status === 'none'" class="verification-prompt">
      <div class="verification-icon">🔒</div>
      <h3>Верификация профиля</h3>
      <p>Подтвердите, что вы реальный человек, и получите синий значок доверия</p>
      <div class="verification-benefits">
        <div class="benefit-item">
          <span class="benefit-icon">📈</span>
          <span>Больше лайков</span>
        </div>
        <div class="benefit-item">
          <span class="benefit-icon">⭐</span>
          <span>Приоритет в поиске</span>
        </div>
        <div class="benefit-item">
          <span class="benefit-icon">🔒</span>
          <span>Повышенное доверие</span>
        </div>
      </div>
      <Button 
        variant="primary" 
        size="lg" 
        @click="startVerification"
        :loading="requesting"
        fullWidth
      >
        Запросить верификацию
      </Button>
    </div>

    <div v-else-if="status === 'pending'" class="verification-pending">
      <div class="verification-icon">⏳</div>
      <h3>Заявка на рассмотрении</h3>
      <p>Ваша заявка на верификацию рассматривается. Обычно это занимает 1-2 дня.</p>
      <div class="verification-status">
        <div class="status-item">
          <span class="status-icon">📤</span>
          <span>Заявка отправлена</span>
          <span class="status-date">{{ formatDate(verificationData.submitted_at) }}</span>
        </div>
        <div class="status-item">
          <span class="status-icon">👀</span>
          <span>На рассмотрении</span>
          <span class="status-date">Скоро</span>
        </div>
      </div>
      <Button 
        variant="outline" 
        size="md" 
        @click="checkStatus"
        :loading="checkingStatus"
      >
        Проверить статус
      </Button>
    </div>

    <div v-else-if="status === 'approved'" class="verification-approved">
      <div class="verification-icon">✅</div>
      <h3>Профиль верифицирован!</h3>
      <p>Поздравляем! Ваш профиль успешно верифицирован.</p>
      <div class="verification-badge-large">
        <span class="badge-icon">✓</span>
        <span class="badge-text">Верифицирован</span>
      </div>
      <div class="verification-details">
        <p><strong>Верифицирован:</strong> {{ formatDate(verificationData.approved_at) }}</p>
        <p><strong>Администратор:</strong> {{ verificationData.approved_by }}</p>
      </div>
    </div>

    <div v-else-if="status === 'rejected'" class="verification-rejected">
      <div class="verification-icon">❌</div>
      <h3>Заявка отклонена</h3>
      <p>К сожалению, ваша заявка на верификацию была отклонена.</p>
      <div class="rejection-reason" v-if="verificationData.rejection_reason">
        <h4>Причина:</h4>
        <p>{{ verificationData.rejection_reason }}</p>
      </div>
      <div class="verification-actions">
        <Button 
          variant="primary" 
          size="md" 
          @click="startVerification"
          :loading="requesting"
        >
          Подать заявку снова
        </Button>
        <Button 
          variant="outline" 
          size="md" 
          @click="contactSupport"
        >
          Связаться с поддержкой
        </Button>
      </div>
    </div>

    <!-- Selfie Upload Modal -->
    <div v-if="showSelfieModal" class="modal-overlay" @click="closeSelfieModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Загрузите селфи</h3>
          <button class="btn btn-icon" @click="closeSelfieModal">✕</button>
        </div>
        
        <div class="modal-body">
          <div class="selfie-instructions">
            <h4>Инструкции для селфи:</h4>
            <ul>
              <li>Сделайте селфи с жестом 🤟</li>
              <li>Лицо должно быть хорошо видно</li>
              <li>Используйте хорошее освещение</li>
              <li>Фото должно быть четким</li>
            </ul>
          </div>
          
          <div class="selfie-upload">
            <input 
              ref="selfieInput"
              type="file" 
              accept="image/*" 
              @change="handleSelfieSelect"
              style="display: none"
            />
            
            <div v-if="!selfiePreview" class="upload-area" @click="selectSelfie">
              <div class="upload-icon">📷</div>
              <p>Нажмите, чтобы выбрать фото</p>
            </div>
            
            <div v-else class="selfie-preview">
              <img :src="selfiePreview" alt="Selfie preview" />
              <button class="btn btn-outline btn-sm" @click="selectSelfie">
                Изменить
              </button>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <Button 
            variant="outline" 
            @click="closeSelfieModal"
          >
            Отмена
          </Button>
          <Button 
            variant="primary" 
            @click="submitVerification"
            :disabled="!selfiePreview || uploading"
            :loading="uploading"
          >
            Отправить
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import Button from '../common/Button.vue'

const userStore = useUserStore()

const props = defineProps({
  verificationData: {
    type: Object,
    default: () => ({})
  }
})

const status = computed(() => props.verificationData.status || 'none')
const requesting = ref(false)
const checkingStatus = ref(false)
const uploading = ref(false)
const showSelfieModal = ref(false)
const selfiePreview = ref(null)
const selfieFile = ref(null)
const selfieInput = ref(null)

const startVerification = () => {
  showSelfieModal.value = true
}

const selectSelfie = () => {
  selfieInput.value?.click()
}

const handleSelfieSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selfieFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      selfiePreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const submitVerification = async () => {
  if (!selfieFile.value) return
  
  uploading.value = true
  try {
    await userStore.requestVerification({
      selfie: selfieFile.value,
      gesture: '🤟'
    })
    showSelfieModal.value = false
    selfiePreview.value = null
    selfieFile.value = null
  } catch (error) {
    console.error('Failed to submit verification:', error)
  } finally {
    uploading.value = false
  }
}

const checkStatus = async () => {
  checkingStatus.value = true
  try {
    await userStore.fetchProfile()
  } finally {
    checkingStatus.value = false
  }
}

const contactSupport = () => {
  // TODO: Implement contact support
  console.log('Contact support')
}

const closeSelfieModal = () => {
  showSelfieModal.value = false
  selfiePreview.value = null
  selfieFile.value = null
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.verification-flow {
  padding: var(--spacing-lg);
}

.verification-prompt,
.verification-pending,
.verification-approved,
.verification-rejected {
  text-align: center;
  padding: var(--spacing-xl);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-lg);
}

.verification-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-lg);
}

.verification-benefits {
  display: flex;
  justify-content: space-around;
  margin: var(--spacing-lg) 0;
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius);
}

.benefit-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
}

.benefit-icon {
  font-size: var(--font-size-lg);
}

.verification-status {
  margin: var(--spacing-lg) 0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius);
}

.status-icon {
  font-size: var(--font-size-md);
}

.status-date {
  margin-left: auto;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.verification-badge-large {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--success-color);
  color: white;
  border-radius: var(--border-radius);
  margin: var(--spacing-lg) 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.badge-icon {
  font-size: var(--font-size-xl);
}

.verification-details {
  text-align: left;
  background-color: var(--bg-primary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  margin-top: var(--spacing-lg);
}

.rejection-reason {
  background-color: rgba(var(--danger-rgb), 0.1);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  margin: var(--spacing-lg) 0;
  text-align: left;
}

.verification-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
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
}

.modal-content {
  background-color: white;
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-body {
  padding: var(--spacing-lg);
}

.selfie-instructions {
  margin-bottom: var(--spacing-lg);
}

.selfie-instructions h4 {
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.selfie-instructions ul {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.selfie-instructions li {
  margin-bottom: var(--spacing-xs);
  color: var(--text-secondary);
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-xl);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.upload-area:hover {
  border-color: var(--primary-color);
}

.upload-icon {
  font-size: 2rem;
  margin-bottom: var(--spacing-sm);
}

.selfie-preview {
  text-align: center;
}

.selfie-preview img {
  width: 100%;
  max-width: 300px;
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-md);
}

.modal-footer {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}
</style>
