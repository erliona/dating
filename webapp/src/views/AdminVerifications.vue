<template>
  <div class="admin-verifications tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <div class="header-left">
        <button class="btn btn-icon" @click="$router.back()">
          ←
        </button>
        <h1>✅ Очередь верификации</h1>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <div class="stats-info">
          <span class="stat-item">
            Ожидают: <strong>{{ pendingCount }}</strong>
          </span>
          <span class="stat-item">
            Одобрены: <strong>{{ approvedCount }}</strong>
          </span>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filters-row">
        <div class="filter-group">
          <label>Статус:</label>
          <select v-model="filters.status" class="filter-select">
            <option value="">Все</option>
            <option value="pending">Ожидают</option>
            <option value="approved">Одобрены</option>
            <option value="rejected">Отклонены</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Сортировка:</label>
          <select v-model="filters.sort" class="filter-select">
            <option value="newest">Новые</option>
            <option value="oldest">Старые</option>
            <option value="risk_score">По риску</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Пользователь:</label>
          <input 
            v-model="filters.user_search" 
            type="text" 
            placeholder="ID или имя..."
            class="filter-input"
          />
        </div>
      </div>
    </div>

    <!-- Verifications List -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка верификаций...</p>
    </div>

    <div v-else-if="verifications.length === 0" class="empty-state">
      <div class="empty-icon">✅</div>
      <h3>Верификации не найдены</h3>
      <p>Попробуйте изменить фильтры</p>
    </div>

    <div v-else class="verifications-list">
      <div 
        v-for="verification in verifications" 
        :key="verification.id"
        class="verification-card"
        :class="getVerificationCardClass(verification)"
      >
        <!-- User Profile Photos -->
        <div class="profile-photos">
          <div class="photos-grid">
            <div 
              v-for="(photo, index) in verification.user.photos" 
              :key="index"
              class="profile-photo"
            >
              <img 
                :src="photo.url" 
                :alt="`Profile photo ${index + 1}`"
                class="photo-image"
              />
            </div>
          </div>
        </div>

        <!-- Verification Selfie -->
        <div class="verification-selfie">
          <div class="selfie-container">
            <img 
              :src="verification.selfie_url" 
              :alt="'Verification selfie'"
              class="selfie-image"
            />
            <div class="selfie-badge">Селфи для верификации</div>
          </div>
        </div>

        <!-- User Info -->
        <div class="user-info">
          <div class="user-header">
            <img 
              :src="getUserAvatar(verification.user)" 
              :alt="verification.user.name"
              class="user-avatar"
            />
            <div class="user-details">
              <div class="user-name">{{ verification.user.name }}</div>
              <div class="user-id">ID: {{ verification.user.id }}</div>
              <div class="user-age">{{ verification.user.age }} лет</div>
            </div>
            <div class="verification-status" :class="getStatusClass(verification.status)">
              {{ getStatusText(verification.status) }}
            </div>
          </div>

          <div class="verification-details">
            <div class="detail-item">
              <span class="detail-label">Заявка подана:</span>
              <span class="detail-value">{{ formatDate(verification.submitted_at) }}</span>
            </div>
            <div class="detail-item" v-if="verification.processed_at">
              <span class="detail-label">Обработана:</span>
              <span class="detail-value">{{ formatDate(verification.processed_at) }}</span>
            </div>
            <div class="detail-item" v-if="verification.processed_by">
              <span class="detail-label">Администратор:</span>
              <span class="detail-value">{{ verification.processed_by }}</span>
            </div>
            <div class="detail-item" v-if="verification.rejection_reason">
              <span class="detail-label">Причина отклонения:</span>
              <span class="detail-value">{{ verification.rejection_reason }}</span>
            </div>
          </div>

          <div class="risk-info" v-if="verification.user.risk_score > 0.3">
            <div class="risk-score" :class="getRiskClass(verification.user.risk_score)">
              Риск пользователя: {{ (verification.user.risk_score * 100).toFixed(0) }}%
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="verification-actions" v-if="verification.status === 'pending'">
          <button 
            class="btn btn-success btn-lg"
            @click="approveVerification(verification)"
          >
            ✅ Одобрить
          </button>
          <button 
            class="btn btn-outline"
            @click="showRejectModal(verification)"
          >
            ❌ Отклонить
          </button>
          <button 
            class="btn btn-danger"
            @click="banUser(verification.user_id)"
          >
            🚫 Заблокировать
          </button>
        </div>

        <div class="verification-actions" v-else-if="verification.status === 'rejected'">
          <button 
            class="btn btn-primary"
            @click="approveVerification(verification)"
          >
            ✅ Одобрить
          </button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <button 
        class="btn btn-outline" 
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        ← Назад
      </button>
      <span class="page-info">
        Страница {{ currentPage }} из {{ totalPages }}
      </span>
      <button 
        class="btn btn-outline" 
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        Вперед →
      </button>
    </div>

    <!-- Reject Modal -->
    <div v-if="showRejectModalFlag" class="modal-overlay" @click="closeRejectModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Отклонить верификацию</h3>
          <button class="btn btn-icon" @click="closeRejectModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Причина отклонения:</label>
            <select v-model="rejectReason" class="form-select">
              <option value="">Выберите причину</option>
              <option value="poor_quality">Плохое качество фото</option>
              <option value="no_gesture">Отсутствует жест 🤟</option>
              <option value="not_matching">Не соответствует профилю</option>
              <option value="suspicious">Подозрительное поведение</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div class="form-group" v-if="rejectReason === 'other'">
            <label>Дополнительные комментарии:</label>
            <textarea 
              v-model="rejectComment" 
              class="form-textarea"
              placeholder="Укажите причину отклонения..."
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeRejectModal">
            Отмена
          </button>
          <button 
            class="btn btn-danger" 
            @click="rejectVerification"
            :disabled="!rejectReason"
          >
            Отклонить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useApi } from '../composables/useApi'

const { get, put } = useApi()

const verifications = ref([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const showRejectModalFlag = ref(false)
const selectedVerification = ref(null)
const rejectReason = ref('')
const rejectComment = ref('')

const filters = ref({
  status: 'pending',
  sort: 'newest',
  user_search: ''
})

const pendingCount = computed(() => 
  verifications.value.filter(v => v.status === 'pending').length
)

const approvedCount = computed(() => 
  verifications.value.filter(v => v.status === 'approved').length
)

const fetchVerifications = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 10,
      ...filters.value
    }
    
    const response = await get('/admin/verifications', { params })
    verifications.value = response.data.verifications
    totalPages.value = response.data.total_pages
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchVerifications()
}

const approveVerification = async (verification) => {
  if (!confirm(`Одобрить верификацию для ${verification.user.name}?`)) return
  
  try {
    await put(`/admin/verifications/${verification.id}/approve`)
    verification.status = 'approved'
    verification.processed_at = new Date().toISOString()
    verification.processed_by = 'Current Admin'
  } catch (error) {
    // Handle error
  }
}

const showRejectModal = (verification) => {
  selectedVerification.value = verification
  showRejectModalFlag.value = true
  rejectReason.value = ''
  rejectComment.value = ''
}

const closeRejectModal = () => {
  showRejectModalFlag.value = false
  selectedVerification.value = null
  rejectReason.value = ''
  rejectComment.value = ''
}

const rejectVerification = async () => {
  if (!selectedVerification.value || !rejectReason.value) return
  
  try {
    await put(`/admin/verifications/${selectedVerification.value.id}/reject`, {
      reason: rejectReason.value,
      comment: rejectComment.value
    })
    
    selectedVerification.value.status = 'rejected'
    selectedVerification.value.rejection_reason = rejectReason.value
    selectedVerification.value.processed_at = new Date().toISOString()
    selectedVerification.value.processed_by = 'Current Admin'
    
    closeRejectModal()
  } catch (error) {
    // Handle error
  }
}

const banUser = async (userId) => {
  if (!confirm('Заблокировать пользователя?')) return
  
  try {
    await put(`/admin/users/${userId}/ban`, { reason: 'Verification fraud' })
    // Refresh data to update user status
    fetchVerifications()
  } catch (error) {
    // Handle error
  }
}

const changePage = (page) => {
  currentPage.value = page
  fetchVerifications()
}

const getUserAvatar = (user) => {
  return user.photos?.[0]?.url || '/default-avatar.png'
}

const getVerificationCardClass = (verification) => {
  const classes = []
  if (verification.status === 'rejected') classes.push('rejected')
  if (verification.user.risk_score > 0.7) classes.push('high-risk')
  return classes
}

const getStatusClass = (status) => {
  switch (status) {
    case 'approved': return 'approved'
    case 'rejected': return 'rejected'
    default: return 'pending'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'approved': return 'Одобрено'
    case 'rejected': return 'Отклонено'
    default: return 'Ожидает'
  }
}

const getRiskClass = (score) => {
  if (score < 0.3) return 'low'
  if (score < 0.7) return 'medium'
  return 'high'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Watch for filter changes
watch(filters, () => {
  currentPage.value = 1
  fetchVerifications()
}, { deep: true })

onMounted(() => {
  fetchVerifications()
})
</script>

<style scoped>
.admin-verifications {
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
  min-height: 100vh;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.admin-header h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stats-info {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.stat-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.filters-section {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  box-shadow: var(--shadow-small);
}

.filters-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.filter-group label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.filter-input,
.filter-select {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.verifications-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.verification-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
  transition: transform 0.2s ease;
}

.verification-card:hover {
  transform: translateY(-2px);
}

.verification-card.rejected {
  opacity: 0.7;
  border-left: 4px solid var(--danger-color);
}

.verification-card.high-risk {
  border-left: 4px solid var(--warning-color);
}

.verification-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
}

.profile-photos {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
}

.profile-photo {
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: var(--border-radius);
}

.photo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.verification-selfie {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.selfie-container {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: var(--border-radius);
  border: 2px solid var(--primary-color);
}

.selfie-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.selfie-badge {
  position: absolute;
  top: var(--spacing-sm);
  left: var(--spacing-sm);
  background-color: var(--primary-color);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.user-info {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.user-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.user-id {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.user-age {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.verification-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  text-align: center;
}

.verification-status.approved {
  background-color: var(--success-color);
  color: white;
}

.verification-status.rejected {
  background-color: var(--danger-color);
  color: white;
}

.verification-status.pending {
  background-color: var(--warning-color);
  color: white;
}

.verification-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
}

.detail-label {
  color: var(--text-secondary);
}

.detail-value {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.risk-info {
  margin-top: var(--spacing-sm);
}

.risk-score {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  text-align: center;
}

.risk-score.low {
  background-color: var(--success-color);
  color: white;
}

.risk-score.medium {
  background-color: var(--warning-color);
  color: white;
}

.risk-score.high {
  background-color: var(--danger-color);
  color: white;
}

.verification-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
}

.page-info {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
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
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.modal-body {
  padding: var(--spacing-md);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-select,
.form-textarea {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}
</style>
