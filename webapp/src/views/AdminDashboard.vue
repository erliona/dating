<template>
  <div class="admin-dashboard tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <h1>🔧 Admin Panel</h1>
      <div class="admin-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <button class="btn btn-primary" @click="logout">
          🚪 Выйти
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_users || 0 }}</div>
          <div class="stat-label">Всего пользователей</div>
          <div class="stat-change" :class="getChangeClass(stats.users_change)">
            {{ formatChange(stats.users_change) }}
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🆕</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.new_users_today || 0 }}</div>
          <div class="stat-label">Новых сегодня</div>
          <div class="stat-change" :class="getChangeClass(stats.new_users_change)">
            {{ formatChange(stats.new_users_change) }}
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💬</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_matches || 0 }}</div>
          <div class="stat-label">Матчей</div>
          <div class="stat-change" :class="getChangeClass(stats.matches_change)">
            {{ formatChange(stats.matches_change) }}
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📨</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_messages || 0 }}</div>
          <div class="stat-label">Сообщений</div>
          <div class="stat-change" :class="getChangeClass(stats.messages_change)">
            {{ formatChange(stats.messages_change) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Alerts Section -->
    <div class="alerts-section">
      <h2>🚨 Требуют внимания</h2>
      <div class="alerts-grid">
        <div class="alert-card" :class="getAlertClass('high')" v-if="alerts.pending_verifications > 0">
          <div class="alert-icon">✅</div>
          <div class="alert-content">
            <div class="alert-title">Верификация</div>
            <div class="alert-count">{{ alerts.pending_verifications }}</div>
            <div class="alert-description">Ожидают одобрения</div>
          </div>
        </div>

        <div class="alert-card" :class="getAlertClass('medium')" v-if="alerts.flagged_profiles > 0">
          <div class="alert-icon">⚠️</div>
          <div class="alert-content">
            <div class="alert-title">Флаги</div>
            <div class="alert-count">{{ alerts.flagged_profiles }}</div>
            <div class="alert-description">Подозрительные профили</div>
          </div>
        </div>

        <div class="alert-card" :class="getAlertClass('high')" v-if="alerts.pending_reports > 0">
          <div class="alert-icon">📋</div>
          <div class="alert-content">
            <div class="alert-title">Жалобы</div>
            <div class="alert-count">{{ alerts.pending_reports }}</div>
            <div class="alert-description">Требуют рассмотрения</div>
          </div>
        </div>

        <div class="alert-card" :class="getAlertClass('medium')" v-if="alerts.nsfw_photos > 0">
          <div class="alert-icon">🔞</div>
          <div class="alert-content">
            <div class="alert-title">NSFW</div>
            <div class="alert-count">{{ alerts.nsfw_photos }}</div>
            <div class="alert-description">Неподходящие фото</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <h2>⚡ Быстрые действия</h2>
      <div class="actions-grid">
        <button class="action-btn" @click="navigateTo('/admin/users')">
          <div class="action-icon">👥</div>
          <div class="action-label">Пользователи</div>
        </button>
        <button class="action-btn" @click="navigateTo('/admin/photos')">
          <div class="action-icon">📸</div>
          <div class="action-label">Модерация фото</div>
        </button>
        <button class="action-btn" @click="navigateTo('/admin/verifications')">
          <div class="action-icon">✅</div>
          <div class="action-label">Верификация</div>
        </button>
        <button class="action-btn" @click="navigateTo('/admin/reports')">
          <div class="action-icon">📋</div>
          <div class="action-label">Жалобы</div>
        </button>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="recent-activity">
      <h2>📊 Последняя активность</h2>
      <div class="activity-list">
        <div 
          v-for="activity in recentActivity" 
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-icon">{{ getActivityIcon(activity.type) }}</div>
          <div class="activity-content">
            <div class="activity-text">{{ activity.description }}</div>
            <div class="activity-time">{{ formatTime(activity.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const router = useRouter()
const { get } = useApi()

const stats = ref({})
const alerts = ref({})
const recentActivity = ref([])
const loading = ref(false)

const fetchDashboardData = async () => {
  loading.value = true
  try {
    // Fetch stats
    const statsResponse = await get('/admin/stats')
    stats.value = statsResponse.data

    // Fetch alerts
    const alertsResponse = await get('/admin/alerts')
    alerts.value = alertsResponse.data

    // Fetch recent activity
    const activityResponse = await get('/admin/activity')
    recentActivity.value = activityResponse.data
  } catch (error) {
    // Handle error
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchDashboardData()
}

const logout = () => {
  localStorage.removeItem('admin_token')
  router.push('/admin/login')
}

const navigateTo = (path) => {
  router.push(path)
}

const getChangeClass = (change) => {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

const formatChange = (change) => {
  if (change > 0) return `+${change}%`
  if (change < 0) return `${change}%`
  return '0%'
}

const getAlertClass = (priority) => {
  return `alert-${priority}`
}

const getActivityIcon = (type) => {
  const icons = {
    'user_registered': '👤',
    'match_created': '💕',
    'message_sent': '💬',
    'verification_approved': '✅',
    'report_created': '📋',
    'user_banned': '🚫'
  }
  return icons[type] || '📝'
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInMinutes = Math.floor((now - date) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'только что'
  if (diffInMinutes < 60) return `${diffInMinutes} мин назад`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} ч назад`
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.admin-dashboard {
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

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.stat-card {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-small);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stat-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
  border-radius: 50%;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.stat-change {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.stat-change.positive {
  color: var(--success-color);
}

.stat-change.negative {
  color: var(--danger-color);
}

.stat-change.neutral {
  color: var(--text-secondary);
}

.alerts-section {
  margin-bottom: var(--spacing-md);
}

.alerts-section h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.alerts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.alert-card {
  background-color: white;
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-small);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  border-left: 4px solid;
}

.alert-card.alert-high {
  border-left-color: var(--danger-color);
}

.alert-card.alert-medium {
  border-left-color: var(--warning-color);
}

.alert-card.alert-low {
  border-left-color: var(--info-color);
}

.alert-icon {
  font-size: var(--font-size-md);
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.alert-count {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.alert-description {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.quick-actions {
  margin-bottom: var(--spacing-md);
}

.quick-actions h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.action-btn {
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.action-icon {
  font-size: var(--font-size-lg);
}

.action-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.recent-activity h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.activity-list {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  font-size: var(--font-size-md);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
  border-radius: 50%;
}

.activity-content {
  flex: 1;
}

.activity-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}
</style>
