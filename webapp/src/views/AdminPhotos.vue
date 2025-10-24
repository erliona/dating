<template>
  <div class="admin-photos tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <div class="header-left">
        <button class="btn btn-icon" @click="$router.back()">
          ←
        </button>
        <h1>📸 Модерация фото</h1>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <div class="keyboard-shortcuts">
          <span class="shortcut">1 - Одобрить</span>
          <span class="shortcut">2 - Отклонить</span>
          <span class="shortcut">3 - Заблокировать</span>
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
          <label>NSFW Score:</label>
          <select v-model="filters.nsfw_level" class="filter-select">
            <option value="">Все</option>
            <option value="safe">Безопасные (< 0.3)</option>
            <option value="suspicious">Подозрительные (0.3-0.7)</option>
            <option value="nsfw">NSFW (> 0.7)</option>
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

        <div class="filter-group">
          <label>Сортировка:</label>
          <select v-model="filters.sort" class="filter-select">
            <option value="newest">Новые</option>
            <option value="oldest">Старые</option>
            <option value="nsfw_score">По NSFW score</option>
            <option value="user_risk">По риску пользователя</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Photos Grid -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка фото...</p>
    </div>

    <div v-else-if="photos.length === 0" class="empty-state">
      <div class="empty-icon">📸</div>
      <h3>Фото не найдены</h3>
      <p>Попробуйте изменить фильтры</p>
    </div>

    <div v-else class="photos-grid">
      <div 
        v-for="photo in photos" 
        :key="photo.id"
        class="photo-card"
        :class="getPhotoCardClass(photo)"
      >
        <!-- Photo -->
        <div class="photo-container">
          <img 
            :src="photo.url" 
            :alt="`Photo ${photo.id}`"
            class="photo-image"
            @click="viewPhoto(photo)"
          />
          <div class="photo-overlay">
            <div class="nsfw-score" :class="getNSFWClass(photo.nsfw_score)">
              NSFW: {{ (photo.nsfw_score * 100).toFixed(0) }}%
            </div>
            <div class="photo-actions">
              <button 
                class="action-btn approve"
                @click="approvePhoto(photo)"
                title="Одобрить (1)"
              >
                ✅
              </button>
              <button 
                class="action-btn reject"
                @click="rejectPhoto(photo)"
                title="Отклонить (2)"
              >
                ❌
              </button>
              <button 
                class="action-btn ban"
                @click="banUser(photo.user_id)"
                title="Заблокировать пользователя (3)"
              >
                🚫
              </button>
            </div>
          </div>
        </div>

        <!-- Photo Info -->
        <div class="photo-info">
          <div class="user-info">
            <img 
              :src="getUserAvatar(photo.user)" 
              :alt="photo.user.name"
              class="user-avatar"
            />
            <div class="user-details">
              <div class="user-name">{{ photo.user.name }}</div>
              <div class="user-id">ID: {{ photo.user.id }}</div>
            </div>
          </div>
          
          <div class="photo-meta">
            <div class="meta-item">
              <span class="meta-label">Загружено:</span>
              <span class="meta-value">{{ formatDate(photo.created_at) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Размер:</span>
              <span class="meta-value">{{ formatFileSize(photo.file_size) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Статус:</span>
              <span class="meta-value" :class="getStatusClass(photo.status)">
                {{ getStatusText(photo.status) }}
              </span>
            </div>
          </div>

          <div class="risk-info" v-if="photo.user.risk_score > 0.3">
            <div class="risk-score" :class="getRiskClass(photo.user.risk_score)">
              Риск пользователя: {{ (photo.user.risk_score * 100).toFixed(0) }}%
            </div>
          </div>
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

    <!-- Photo Viewer Modal -->
    <div v-if="selectedPhoto" class="modal-overlay" @click="closePhotoModal">
      <div class="modal-content photo-viewer" @click.stop>
        <div class="modal-header">
          <h3>Фото {{ selectedPhoto.id }}</h3>
          <button class="btn btn-icon" @click="closePhotoModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="photo-viewer-container">
            <img 
              :src="selectedPhoto.url" 
              :alt="`Photo ${selectedPhoto.id}`"
              class="photo-viewer-image"
            />
          </div>
          <div class="photo-details">
            <div class="detail-section">
              <h4>Информация о фото</h4>
              <div class="detail-item">
                <span class="detail-label">NSFW Score:</span>
                <span class="detail-value" :class="getNSFWClass(selectedPhoto.nsfw_score)">
                  {{ (selectedPhoto.nsfw_score * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Размер файла:</span>
                <span class="detail-value">{{ formatFileSize(selectedPhoto.file_size) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Загружено:</span>
                <span class="detail-value">{{ formatDate(selectedPhoto.created_at) }}</span>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>Пользователь</h4>
              <div class="user-card">
                <img 
                  :src="getUserAvatar(selectedPhoto.user)" 
                  :alt="selectedPhoto.user.name"
                  class="user-avatar-large"
                />
                <div class="user-info">
                  <div class="user-name">{{ selectedPhoto.user.name }}</div>
                  <div class="user-id">ID: {{ selectedPhoto.user.id }}</div>
                  <div class="user-risk" :class="getRiskClass(selectedPhoto.user.risk_score)">
                    Риск: {{ (selectedPhoto.user.risk_score * 100).toFixed(0) }}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closePhotoModal">
            Закрыть
          </button>
          <button class="btn btn-danger" @click="rejectPhoto(selectedPhoto)">
            Отклонить
          </button>
          <button class="btn btn-success" @click="approvePhoto(selectedPhoto)">
            Одобрить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useApi } from '../composables/useApi'

const { get, put } = useApi()

const photos = ref([])
const selectedPhoto = ref(null)
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)

const filters = ref({
  status: 'pending',
  nsfw_level: '',
  user_search: '',
  sort: 'newest'
})

const fetchPhotos = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 12,
      ...filters.value
    }
    
    const response = await get('/admin/photos', { params })
    photos.value = response.data.photos
    totalPages.value = response.data.total_pages
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchPhotos()
}

const viewPhoto = (photo) => {
  selectedPhoto.value = photo
}

const closePhotoModal = () => {
  selectedPhoto.value = null
}

const approvePhoto = async (photo) => {
  try {
    await put(`/admin/photos/${photo.id}/approve`)
    photo.status = 'approved'
    // Remove from current view if filtering by pending
    if (filters.value.status === 'pending') {
      const index = photos.value.findIndex(p => p.id === photo.id)
      if (index > -1) {
        photos.value.splice(index, 1)
      }
    }
  } catch (error) {
    // Handle error
  }
}

const rejectPhoto = async (photo) => {
  try {
    await put(`/admin/photos/${photo.id}/reject`)
    photo.status = 'rejected'
    // Remove from current view if filtering by pending
    if (filters.value.status === 'pending') {
      const index = photos.value.findIndex(p => p.id === photo.id)
      if (index > -1) {
        photos.value.splice(index, 1)
      }
    }
  } catch (error) {
    // Handle error
  }
}

const banUser = async (userId) => {
  if (!confirm('Заблокировать пользователя?')) return
  
  try {
    await put(`/admin/users/${userId}/ban`, { reason: 'NSFW content' })
    // Refresh data to update user status
    fetchPhotos()
  } catch (error) {
    // Handle error
  }
}

const changePage = (page) => {
  currentPage.value = page
  fetchPhotos()
}

const getUserAvatar = (user) => {
  return user.photos?.[0]?.url || '/default-avatar.png'
}

const getPhotoCardClass = (photo) => {
  const classes = []
  if (photo.nsfw_score > 0.7) classes.push('nsfw')
  if (photo.user.risk_score > 0.7) classes.push('high-risk')
  if (photo.status === 'rejected') classes.push('rejected')
  return classes
}

const getNSFWClass = (score) => {
  if (score < 0.3) return 'safe'
  if (score < 0.7) return 'suspicious'
  return 'nsfw'
}

const getRiskClass = (score) => {
  if (score < 0.3) return 'low'
  if (score < 0.7) return 'medium'
  return 'high'
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

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// Keyboard shortcuts
const handleKeyPress = (event) => {
  if (!selectedPhoto.value) return
  
  switch (event.key) {
    case '1':
      approvePhoto(selectedPhoto.value)
      break
    case '2':
      rejectPhoto(selectedPhoto.value)
      break
    case '3':
      banUser(selectedPhoto.value.user_id)
      break
  }
}

// Watch for filter changes
watch(filters, () => {
  currentPage.value = 1
  fetchPhotos()
}, { deep: true })

onMounted(() => {
  fetchPhotos()
  document.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
})
</script>

<style scoped>
.admin-photos {
  padding: var(--spacing-lg);
  background-color: var(--bg-primary);
  min-height: 100vh;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.admin-header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.keyboard-shortcuts {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.shortcut {
  padding: 2px 6px;
  background-color: var(--bg-secondary);
  border-radius: 4px;
}

.filters-section {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
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
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-lg);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.photo-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
  transition: transform 0.2s ease;
}

.photo-card:hover {
  transform: translateY(-2px);
}

.photo-card.nsfw {
  border: 2px solid var(--danger-color);
}

.photo-card.high-risk {
  border: 2px solid var(--warning-color);
}

.photo-card.rejected {
  opacity: 0.7;
}

.photo-container {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
}

.photo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.photo-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 50%, rgba(0,0,0,0.7) 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--spacing-sm);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.photo-container:hover .photo-overlay {
  opacity: 1;
}

.nsfw-score {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  text-align: center;
}

.nsfw-score.safe {
  background-color: var(--success-color);
  color: white;
}

.nsfw-score.suspicious {
  background-color: var(--warning-color);
  color: white;
}

.nsfw-score.nsfw {
  background-color: var(--danger-color);
  color: white;
}

.photo-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-sm);
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: transform 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.1);
}

.action-btn.approve {
  background-color: var(--success-color);
  color: white;
}

.action-btn.reject {
  background-color: var(--danger-color);
  color: white;
}

.action-btn.ban {
  background-color: var(--warning-color);
  color: white;
}

.photo-info {
  padding: var(--spacing-md);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.user-name {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.user-id {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.photo-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.meta-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
}

.meta-label {
  color: var(--text-secondary);
}

.meta-value {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.meta-value.approved {
  color: var(--success-color);
}

.meta-value.rejected {
  color: var(--danger-color);
}

.meta-value.pending {
  color: var(--warning-color);
}

.risk-info {
  margin-top: var(--spacing-sm);
}

.risk-score {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
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

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
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
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: var(--border-radius);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.photo-viewer {
  max-width: 1000px;
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

.photo-viewer-container {
  text-align: center;
  margin-bottom: var(--spacing-lg);
}

.photo-viewer-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-medium);
}

.photo-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.detail-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.detail-label {
  color: var(--text-secondary);
}

.detail-value {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.user-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.user-avatar-large {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.user-id {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.user-risk {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  padding: 2px 6px;
  border-radius: 8px;
}

.user-risk.low {
  background-color: var(--success-color);
  color: white;
}

.user-risk.medium {
  background-color: var(--warning-color);
  color: white;
}

.user-risk.high {
  background-color: var(--danger-color);
  color: white;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}
</style>
