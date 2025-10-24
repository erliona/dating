<template>
  <div class="admin-users tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <div class="header-left">
        <button class="btn btn-icon" @click="$router.back()">
          ←
        </button>
        <h1>👥 Управление пользователями</h1>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <button class="btn btn-primary" @click="exportUsers">
          📊 Экспорт
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filters-row">
        <div class="filter-group">
          <label>Поиск:</label>
          <input 
            v-model="filters.search" 
            type="text" 
            placeholder="Имя, email, ID..."
            class="filter-input"
          />
        </div>
        
        <div class="filter-group">
          <label>Статус:</label>
          <select v-model="filters.status" class="filter-select">
            <option value="">Все</option>
            <option value="active">Активные</option>
            <option value="banned">Заблокированные</option>
            <option value="flagged">Подозрительные</option>
            <option value="verified">Верифицированные</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Риск:</label>
          <select v-model="filters.risk_level" class="filter-select">
            <option value="">Все</option>
            <option value="low">Низкий (< 0.3)</option>
            <option value="medium">Средний (0.3-0.7)</option>
            <option value="high">Высокий (> 0.7)</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Город:</label>
          <input 
            v-model="filters.city" 
            type="text" 
            placeholder="Москва..."
            class="filter-input"
          />
        </div>
      </div>
    </div>

    <!-- Users Table -->
    <div class="users-table-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка пользователей...</p>
      </div>

      <div v-else-if="users.length === 0" class="empty-state">
        <div class="empty-icon">👥</div>
        <h3>Пользователи не найдены</h3>
        <p>Попробуйте изменить фильтры</p>
      </div>

      <div v-else class="users-table">
        <div class="table-header">
          <div class="col-id">ID</div>
          <div class="col-name">Имя</div>
          <div class="col-age">Возраст</div>
          <div class="col-city">Город</div>
          <div class="col-status">Статус</div>
          <div class="col-risk">Риск</div>
          <div class="col-created">Создан</div>
          <div class="col-actions">Действия</div>
        </div>

        <div 
          v-for="user in users" 
          :key="user.id"
          class="table-row"
          :class="{ 'flagged': user.is_flagged, 'banned': user.is_banned }"
        >
          <div class="col-id">{{ user.id }}</div>
          <div class="col-name">
            <div class="user-info">
              <img 
                :src="getUserAvatar(user)" 
                :alt="user.name"
                class="user-avatar"
              />
              <div class="user-details">
                <div class="user-name">{{ user.name }}</div>
                <div class="user-username" v-if="user.telegram_username">
                  @{{ user.telegram_username }}
                </div>
              </div>
            </div>
          </div>
          <div class="col-age">{{ user.age }}</div>
          <div class="col-city">{{ user.city }}</div>
          <div class="col-status">
            <div class="status-badges">
              <span v-if="user.is_verified" class="badge verified">✓</span>
              <span v-if="user.is_banned" class="badge banned">🚫</span>
              <span v-if="user.is_flagged" class="badge flagged">⚠️</span>
            </div>
          </div>
          <div class="col-risk">
            <div 
              class="risk-score" 
              :class="getRiskClass(user.risk_score)"
            >
              {{ (user.risk_score * 100).toFixed(0) }}%
            </div>
          </div>
          <div class="col-created">{{ formatDate(user.created_at) }}</div>
          <div class="col-actions">
            <div class="action-buttons">
              <button 
                class="btn btn-sm btn-outline" 
                @click="viewUser(user)"
                title="Просмотр"
              >
                👁️
              </button>
              <button 
                class="btn btn-sm btn-outline" 
                @click="viewMetadata(user)"
                title="Метаданные"
              >
                📊
              </button>
              <button 
                v-if="!user.is_banned"
                class="btn btn-sm btn-danger" 
                @click="banUser(user)"
                title="Заблокировать"
              >
                🚫
              </button>
              <button 
                v-else
                class="btn btn-sm btn-success" 
                @click="unbanUser(user)"
                title="Разблокировать"
              >
                ✅
              </button>
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

    <!-- User Details Modal -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeUserModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Детали пользователя</h3>
          <button class="btn btn-icon" @click="closeUserModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="user-profile">
            <img 
              :src="getUserAvatar(selectedUser)" 
              :alt="selectedUser.name"
              class="profile-avatar"
            />
            <div class="profile-info">
              <h4>{{ selectedUser.name }}</h4>
              <p v-if="selectedUser.telegram_username">@{{ selectedUser.telegram_username }}</p>
              <p>Возраст: {{ selectedUser.age }}</p>
              <p>Город: {{ selectedUser.city }}</p>
              <p>Создан: {{ formatDate(selectedUser.created_at) }}</p>
            </div>
          </div>
          
          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-label">Матчи:</span>
              <span class="stat-value">{{ selectedUser.matches_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Сообщения:</span>
              <span class="stat-value">{{ selectedUser.messages_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Лайки:</span>
              <span class="stat-value">{{ selectedUser.likes_given || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const router = useRouter()
const { get, put } = useApi()

const users = ref([])
const selectedUser = ref(null)
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const totalUsers = ref(0)

const filters = ref({
  search: '',
  status: '',
  risk_level: '',
  city: ''
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 20,
      ...filters.value
    }
    
    const response = await get('/admin/users', { params })
    users.value = response.data.users
    totalPages.value = response.data.total_pages
    totalUsers.value = response.data.total_users
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchUsers()
}

const exportUsers = () => {
// TODO: Implement export functionality
}

const viewUser = (user) => {
  selectedUser.value = user
}

const closeUserModal = () => {
  selectedUser.value = null
}

const viewMetadata = (user) => {
  router.push(`/admin/users/${user.id}/metadata`)
}

const banUser = async (user) => {
  if (!confirm(`Заблокировать пользователя ${user.name}?`)) return
  
  try {
    await put(`/admin/users/${user.id}/ban`, { reason: 'Admin action' })
    user.is_banned = true
  } catch (error) {
    // Handle error
  }
}

const unbanUser = async (user) => {
  if (!confirm(`Разблокировать пользователя ${user.name}?`)) return
  
  try {
    await put(`/admin/users/${user.id}/unban`)
    user.is_banned = false
  } catch (error) {
    // Handle error
  }
}

const changePage = (page) => {
  currentPage.value = page
  fetchUsers()
}

const getUserAvatar = (user) => {
  return user.photos?.[0]?.url || '/default-avatar.png'
}

const getRiskClass = (riskScore) => {
  if (riskScore < 0.3) return 'low'
  if (riskScore < 0.7) return 'medium'
  return 'high'
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU')
}

// Watch for filter changes
watch(filters, () => {
  currentPage.value = 1
  fetchUsers()
}, { deep: true })

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.admin-users {
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
  gap: var(--spacing-sm);
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

.users-table-container {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
  margin-bottom: var(--spacing-lg);
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

.users-table {
  overflow-x: auto;
}

.table-header {
  display: grid;
  grid-template-columns: 60px 1fr 80px 120px 120px 80px 120px 120px;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.table-row {
  display: grid;
  grid-template-columns: 60px 1fr 80px 120px 120px 80px 120px 120px;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  align-items: center;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: var(--bg-secondary);
}

.table-row.flagged {
  background-color: rgba(var(--warning-rgb), 0.1);
}

.table-row.banned {
  background-color: rgba(var(--danger-rgb), 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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

.user-username {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.status-badges {
  display: flex;
  gap: var(--spacing-xs);
}

.badge {
  padding: 2px 6px;
  border-radius: 10px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.badge.verified {
  background-color: var(--success-color);
  color: white;
}

.badge.banned {
  background-color: var(--danger-color);
  color: white;
}

.badge.flagged {
  background-color: var(--warning-color);
  color: white;
}

.risk-score {
  padding: 2px 6px;
  border-radius: 10px;
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

.action-buttons {
  display: flex;
  gap: var(--spacing-xs);
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
  max-width: 600px;
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

.user-profile {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.profile-info h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.profile-info p {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.user-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.stat-label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  display: block;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}
</style>
