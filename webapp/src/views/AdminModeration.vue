<template>
  <div class="admin-moderation tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <h1>⏳ Модерация</h1>
      <div class="admin-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <button class="btn btn-primary" @click="navigateTo('/admin')">
          🏠 Дашборд
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filter-group">
        <label>Статус:</label>
        <select v-model="filters.status" @change="applyFilters">
          <option value="pending">Ожидают</option>
          <option value="approved">Одобрены</option>
          <option value="rejected">Отклонены</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>Тип контента:</label>
        <select v-model="filters.content_type" @change="applyFilters">
          <option value="">Все</option>
          <option value="photo">Фото</option>
          <option value="profile">Профили</option>
          <option value="report">Жалобы</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>Приоритет:</label>
        <select v-model="filters.priority" @change="applyFilters">
          <option value="">Все</option>
          <option value="3">Высокий</option>
          <option value="2">Средний</option>
          <option value="1">Низкий</option>
        </select>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="stat-item">
        <span class="stat-label">Всего:</span>
        <span class="stat-value">{{ stats.total }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Ожидают:</span>
        <span class="stat-value pending">{{ stats.pending }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Одобрены:</span>
        <span class="stat-value approved">{{ stats.approved }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Отклонены:</span>
        <span class="stat-value rejected">{{ stats.rejected }}</span>
      </div>
    </div>

    <!-- Moderation Queue -->
    <div class="moderation-queue">
      <div class="queue-header">
        <h2>📋 Очередь модерации</h2>
        <div class="pagination-info">
          Показано {{ items.length }} из {{ total }}
        </div>
      </div>

      <div class="queue-list" v-if="!loading">
        <div 
          v-for="item in items" 
          :key="item.id"
          class="moderation-item"
          :class="getItemClass(item)"
        >
          <div class="item-header">
            <div class="item-type">
              <span class="type-icon">{{ getTypeIcon(item.content_type) }}</span>
              <span class="type-label">{{ getTypeLabel(item.content_type) }}</span>
            </div>
            <div class="item-priority" :class="getPriorityClass(item.priority)">
              {{ getPriorityLabel(item.priority) }}
            </div>
          </div>

          <div class="item-content">
            <div class="item-info">
              <div class="info-row">
                <span class="info-label">ID:</span>
                <span class="info-value">{{ item.content_id }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Пользователь:</span>
                <span class="info-value">{{ item.user_id }}</span>
              </div>
              <div class="info-row" v-if="item.reason">
                <span class="info-label">Причина:</span>
                <span class="info-value">{{ getReasonLabel(item.reason) }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Создано:</span>
                <span class="info-value">{{ formatDate(item.created_at) }}</span>
              </div>
            </div>

            <div class="item-actions" v-if="item.status === 'pending'">
              <button 
                class="btn btn-success btn-sm" 
                @click="approveItem(item)"
                :disabled="processing"
              >
                ✅ Одобрить
              </button>
              <button 
                class="btn btn-danger btn-sm" 
                @click="rejectItem(item)"
                :disabled="processing"
              >
                ❌ Отклонить
              </button>
            </div>

            <div class="item-status" v-else>
              <div class="status-info">
                <span class="status-label">Статус:</span>
                <span class="status-value" :class="getStatusClass(item.status)">
                  {{ getStatusLabel(item.status) }}
                </span>
              </div>
              <div class="status-info" v-if="item.moderator_id">
                <span class="status-label">Модератор:</span>
                <span class="status-value">{{ item.moderator_id }}</span>
              </div>
              <div class="status-info" v-if="item.moderated_at">
                <span class="status-label">Дата:</span>
                <span class="status-value">{{ formatDate(item.moderated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="loading-state" v-if="loading">
        <div class="loading-spinner">⏳</div>
        <div class="loading-text">Загрузка...</div>
      </div>

      <div class="empty-state" v-if="!loading && items.length === 0">
        <div class="empty-icon">📭</div>
        <div class="empty-text">Нет элементов для модерации</div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="total > limit">
      <button 
        class="btn btn-outline" 
        @click="loadPage(currentPage - 1)"
        :disabled="currentPage <= 1"
      >
        ← Назад
      </button>
      <span class="page-info">
        Страница {{ currentPage }} из {{ totalPages }}
      </span>
      <button 
        class="btn btn-outline" 
        @click="loadPage(currentPage + 1)"
        :disabled="currentPage >= totalPages"
      >
        Вперед →
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useApi } from '../composables/useApi'

const { get, post } = useApi()

const items = ref([])
const stats = ref({})
const loading = ref(false)
const processing = ref(false)
const total = ref(0)
const currentPage = ref(1)
const limit = 20

const filters = ref({
  status: 'pending',
  content_type: '',
  priority: ''
})

const totalPages = computed(() => Math.ceil(total.value / limit))

const fetchModerationData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      status: filters.value.status,
      page: currentPage.value,
      limit: limit
    })
    
    if (filters.value.content_type) {
      params.append('content_type', filters.value.content_type)
    }
    if (filters.value.priority) {
      params.append('priority', filters.value.priority)
    }

    const response = await get(`/admin/moderation/queue?${params}`)
    items.value = response.data.items || []
    total.value = response.data.total || 0
    
    // Calculate stats
    stats.value = {
      total: total.value,
      pending: items.value.filter(item => item.status === 'pending').length,
      approved: items.value.filter(item => item.status === 'approved').length,
      rejected: items.value.filter(item => item.status === 'rejected').length
    }
  } catch (error) {
    console.error('Error fetching moderation data:', error)
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  currentPage.value = 1
  fetchModerationData()
}

const loadPage = (page) => {
  currentPage.value = page
  fetchModerationData()
}

const approveItem = async (item) => {
  processing.value = true
  try {
    await post(`/admin/moderation/${item.id}/approve`, {
      moderator_id: 'current_admin', // TODO: Get from auth
      notes: 'Approved via admin panel'
    })
    
    // Update item status
    item.status = 'approved'
    item.moderator_id = 'current_admin'
    item.moderated_at = new Date().toISOString()
    
    // Refresh stats
    fetchModerationData()
  } catch (error) {
    console.error('Error approving item:', error)
  } finally {
    processing.value = false
  }
}

const rejectItem = async (item) => {
  processing.value = true
  try {
    await post(`/admin/moderation/${item.id}/reject`, {
      moderator_id: 'current_admin', // TODO: Get from auth
      notes: 'Rejected via admin panel'
    })
    
    // Update item status
    item.status = 'rejected'
    item.moderator_id = 'current_admin'
    item.moderated_at = new Date().toISOString()
    
    // Refresh stats
    fetchModerationData()
  } catch (error) {
    console.error('Error rejecting item:', error)
  } finally {
    processing.value = false
  }
}

const refreshData = () => {
  fetchModerationData()
}

const navigateTo = (path) => {
  // TODO: Use router
  window.location.href = path
}

const getTypeIcon = (type) => {
  const icons = {
    'photo': '📸',
    'profile': '👤',
    'report': '📋'
  }
  return icons[type] || '📄'
}

const getTypeLabel = (type) => {
  const labels = {
    'photo': 'Фото',
    'profile': 'Профиль',
    'report': 'Жалоба'
  }
  return labels[type] || type
}

const getPriorityClass = (priority) => {
  if (priority >= 3) return 'priority-high'
  if (priority >= 2) return 'priority-medium'
  return 'priority-low'
}

const getPriorityLabel = (priority) => {
  if (priority >= 3) return 'Высокий'
  if (priority >= 2) return 'Средний'
  return 'Низкий'
}

const getReasonLabel = (reason) => {
  const labels = {
    'upload': 'Загрузка',
    'profile_update': 'Обновление профиля',
    'report': 'Жалоба',
    'verification': 'Верификация'
  }
  return labels[reason] || reason
}

const getStatusClass = (status) => {
  return `status-${status}`
}

const getStatusLabel = (status) => {
  const labels = {
    'pending': 'Ожидает',
    'approved': 'Одобрено',
    'rejected': 'Отклонено'
  }
  return labels[status] || status
}

const getItemClass = (item) => {
  return `item-${item.status}`
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU')
}

onMounted(() => {
  fetchModerationData()
})
</script>

<style scoped>
.admin-moderation {
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

.admin-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.admin-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.filters-section {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  min-width: 150px;
}

.filter-group label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.filter-group select {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.stats-section {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.stat-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
}

.stat-value.pending {
  color: var(--warning-color);
}

.stat-value.approved {
  color: var(--success-color);
}

.stat-value.rejected {
  color: var(--danger-color);
}

.moderation-queue {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.queue-header h2 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.pagination-info {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.queue-list {
  max-height: 600px;
  overflow-y: auto;
}

.moderation-item {
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-md);
  transition: background-color 0.2s ease;
}

.moderation-item:hover {
  background-color: var(--bg-secondary);
}

.moderation-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.item-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.type-icon {
  font-size: var(--font-size-md);
}

.type-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.item-priority {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.priority-high {
  background-color: var(--danger-color);
  color: white;
}

.priority-medium {
  background-color: var(--warning-color);
  color: white;
}

.priority-low {
  background-color: var(--info-color);
  color: white;
}

.item-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.item-info {
  flex: 1;
}

.info-row {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.info-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  min-width: 100px;
}

.info-value {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  font-family: monospace;
}

.item-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.item-status {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  min-width: 200px;
}

.status-info {
  display: flex;
  gap: var(--spacing-sm);
}

.status-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  min-width: 80px;
}

.status-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-pending {
  color: var(--warning-color);
}

.status-approved {
  color: var(--success-color);
}

.status-rejected {
  color: var(--danger-color);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
}

.loading-spinner {
  font-size: var(--font-size-2xl);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
}

.empty-icon {
  font-size: var(--font-size-2xl);
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: white;
  border-top: 1px solid var(--border-color);
}

.page-info {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background-color: transparent;
  color: var(--text-primary);
}

.btn-outline:hover:not(:disabled) {
  background-color: var(--bg-secondary);
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.btn-success {
  background-color: var(--success-color);
  color: white;
  border-color: var(--success-color);
}

.btn-success:hover:not(:disabled) {
  background-color: var(--success-dark);
}

.btn-danger {
  background-color: var(--danger-color);
  color: white;
  border-color: var(--danger-color);
}

.btn-danger:hover:not(:disabled) {
  background-color: var(--danger-dark);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
}
</style>
