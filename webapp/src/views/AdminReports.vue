<template>
  <div class="admin-reports tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="admin-header">
      <div class="header-left">
        <button class="btn btn-icon" @click="$router.back()">
          ←
        </button>
        <h1>📋 Управление жалобами</h1>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshData">
          🔄 Обновить
        </button>
        <div class="stats-info">
          <span class="stat-item">
            Новые: <strong>{{ newReportsCount }}</strong>
          </span>
          <span class="stat-item">
            В работе: <strong>{{ inProgressCount }}</strong>
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
            <option value="pending">Новые</option>
            <option value="investigating">В работе</option>
            <option value="resolved">Решены</option>
            <option value="dismissed">Отклонены</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Тип жалобы:</label>
          <select v-model="filters.report_type" class="filter-select">
            <option value="">Все</option>
            <option value="inappropriate_content">Неподходящий контент</option>
            <option value="harassment">Притеснение</option>
            <option value="fake_profile">Фейковый профиль</option>
            <option value="spam">Спам</option>
            <option value="other">Другое</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Сортировка:</label>
          <select v-model="filters.sort" class="filter-select">
            <option value="newest">Новые</option>
            <option value="oldest">Старые</option>
            <option value="priority">По приоритету</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Поиск:</label>
          <input 
            v-model="filters.search" 
            type="text" 
            placeholder="ID, имя пользователя..."
            class="filter-input"
          />
        </div>
      </div>
    </div>

    <!-- Reports List -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка жалоб...</p>
    </div>

    <div v-else-if="reports.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>Жалобы не найдены</h3>
      <p>Попробуйте изменить фильтры</p>
    </div>

    <div v-else class="reports-list">
      <div 
        v-for="report in reports" 
        :key="report.id"
        class="report-card"
        :class="getReportCardClass(report)"
      >
        <!-- Report Header -->
        <div class="report-header">
          <div class="report-info">
            <div class="report-id">#{{ report.id }}</div>
            <div class="report-type" :class="getReportTypeClass(report.report_type)">
              {{ getReportTypeText(report.report_type) }}
            </div>
            <div class="report-priority" :class="getPriorityClass(report.priority)">
              {{ getPriorityText(report.priority) }}
            </div>
          </div>
          <div class="report-status" :class="getStatusClass(report.status)">
            {{ getStatusText(report.status) }}
          </div>
        </div>

        <!-- Report Content -->
        <div class="report-content">
          <div class="reporter-info">
            <div class="user-card">
              <img 
                :src="getUserAvatar(report.reporter)" 
                :alt="report.reporter.name"
                class="user-avatar"
              />
              <div class="user-details">
                <div class="user-name">{{ report.reporter.name }}</div>
                <div class="user-id">ID: {{ report.reporter.id }}</div>
                <div class="report-date">{{ formatDate(report.created_at) }}</div>
              </div>
            </div>
          </div>

          <div class="reported-info">
            <div class="user-card">
              <img 
                :src="getUserAvatar(report.reported_user)" 
                :alt="report.reported_user.name"
                class="user-avatar"
              />
              <div class="user-details">
                <div class="user-name">{{ report.reported_user.name }}</div>
                <div class="user-id">ID: {{ report.reported_user.id }}</div>
                <div class="user-risk" :class="getRiskClass(report.reported_user.risk_score)">
                  Риск: {{ (report.reported_user.risk_score * 100).toFixed(0) }}%
                </div>
              </div>
            </div>
          </div>

          <div class="report-reason">
            <h4>Причина жалобы:</h4>
            <p>{{ report.reason }}</p>
          </div>

          <div class="report-evidence" v-if="report.evidence">
            <h4>Доказательства:</h4>
            <div class="evidence-content">
              <div v-if="report.evidence.screenshots" class="screenshots">
                <img 
                  v-for="(screenshot, index) in report.evidence.screenshots" 
                  :key="index"
                  :src="screenshot" 
                  :alt="`Screenshot ${index + 1}`"
                  class="screenshot"
                  @click="viewScreenshot(screenshot)"
                />
              </div>
              <div v-if="report.evidence.message_content" class="message-content">
                <strong>Сообщение:</strong>
                <p>{{ report.evidence.message_content }}</p>
              </div>
            </div>
          </div>

          <div class="report-notes" v-if="report.admin_notes">
            <h4>Заметки администратора:</h4>
            <p>{{ report.admin_notes }}</p>
          </div>
        </div>

        <!-- Report Actions -->
        <div class="report-actions" v-if="report.status === 'pending' || report.status === 'investigating'">
          <button 
            class="btn btn-primary"
            @click="startInvestigation(report)"
          >
            🔍 Начать расследование
          </button>
          <button 
            class="btn btn-success"
            @click="resolveReport(report)"
          >
            ✅ Решить
          </button>
          <button 
            class="btn btn-outline"
            @click="showDismissModal(report)"
          >
            ❌ Отклонить
          </button>
          <button 
            class="btn btn-danger"
            @click="banReportedUser(report)"
          >
            🚫 Заблокировать
          </button>
        </div>

        <div class="report-actions" v-else-if="report.status === 'resolved'">
          <button 
            class="btn btn-outline"
            @click="reopenReport(report)"
          >
            🔄 Переоткрыть
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

    <!-- Dismiss Modal -->
    <div v-if="showDismissModalFlag" class="modal-overlay" @click="closeDismissModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Отклонить жалобу</h3>
          <button class="btn btn-icon" @click="closeDismissModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Причина отклонения:</label>
            <select v-model="dismissReason" class="form-select">
              <option value="">Выберите причину</option>
              <option value="no_violation">Нарушений не обнаружено</option>
              <option value="false_report">Ложная жалоба</option>
              <option value="insufficient_evidence">Недостаточно доказательств</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div class="form-group" v-if="dismissReason === 'other'">
            <label>Дополнительные комментарии:</label>
            <textarea 
              v-model="dismissComment" 
              class="form-textarea"
              placeholder="Укажите причину отклонения..."
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeDismissModal">
            Отмена
          </button>
          <button 
            class="btn btn-danger" 
            @click="dismissReport"
            :disabled="!dismissReason"
          >
            Отклонить
          </button>
        </div>
      </div>
    </div>

    <!-- Screenshot Viewer -->
    <div v-if="selectedScreenshot" class="modal-overlay" @click="closeScreenshotViewer">
      <div class="modal-content screenshot-viewer" @click.stop>
        <div class="modal-header">
          <h3>Скриншот</h3>
          <button class="btn btn-icon" @click="closeScreenshotViewer">✕</button>
        </div>
        <div class="modal-body">
          <img 
            :src="selectedScreenshot" 
            alt="Screenshot"
            class="screenshot-image"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useApi } from '../composables/useApi'

const { get, put } = useApi()

const reports = ref([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const showDismissModalFlag = ref(false)
const selectedReport = ref(null)
const dismissReason = ref('')
const dismissComment = ref('')
const selectedScreenshot = ref(null)

const filters = ref({
  status: 'pending',
  report_type: '',
  sort: 'newest',
  search: ''
})

const newReportsCount = computed(() => 
  reports.value.filter(r => r.status === 'pending').length
)

const inProgressCount = computed(() => 
  reports.value.filter(r => r.status === 'investigating').length
)

const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: 10,
      ...filters.value
    }
    
    const response = await get('/admin/reports', { params })
    reports.value = response.data.reports
    totalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to fetch reports:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchReports()
}

const startInvestigation = async (report) => {
  try {
    await put(`/admin/reports/${report.id}/investigate`)
    report.status = 'investigating'
  } catch (error) {
    console.error('Failed to start investigation:', error)
  }
}

const resolveReport = async (report) => {
  if (!confirm(`Отметить жалобу #${report.id} как решенную?`)) return
  
  try {
    await put(`/admin/reports/${report.id}/resolve`)
    report.status = 'resolved'
  } catch (error) {
    console.error('Failed to resolve report:', error)
  }
}

const showDismissModal = (report) => {
  selectedReport.value = report
  showDismissModalFlag.value = true
  dismissReason.value = ''
  dismissComment.value = ''
}

const closeDismissModal = () => {
  showDismissModalFlag.value = false
  selectedReport.value = null
  dismissReason.value = ''
  dismissComment.value = ''
}

const dismissReport = async () => {
  if (!selectedReport.value || !dismissReason.value) return
  
  try {
    await put(`/admin/reports/${selectedReport.value.id}/dismiss`, {
      reason: dismissReason.value,
      comment: dismissComment.value
    })
    
    selectedReport.value.status = 'dismissed'
    closeDismissModal()
  } catch (error) {
    console.error('Failed to dismiss report:', error)
  }
}

const banReportedUser = async (report) => {
  if (!confirm(`Заблокировать пользователя ${report.reported_user.name}?`)) return
  
  try {
    await put(`/admin/users/${report.reported_user.id}/ban`, { 
      reason: `Reported: ${report.reason}` 
    })
    // Mark report as resolved
    await put(`/admin/reports/${report.id}/resolve`)
    report.status = 'resolved'
  } catch (error) {
    console.error('Failed to ban user:', error)
  }
}

const reopenReport = async (report) => {
  try {
    await put(`/admin/reports/${report.id}/reopen`)
    report.status = 'pending'
  } catch (error) {
    console.error('Failed to reopen report:', error)
  }
}

const viewScreenshot = (screenshot) => {
  selectedScreenshot.value = screenshot
}

const closeScreenshotViewer = () => {
  selectedScreenshot.value = null
}

const changePage = (page) => {
  currentPage.value = page
  fetchReports()
}

const getUserAvatar = (user) => {
  return user.photos?.[0]?.url || '/default-avatar.png'
}

const getReportCardClass = (report) => {
  const classes = []
  if (report.priority === 'high') classes.push('high-priority')
  if (report.status === 'resolved') classes.push('resolved')
  if (report.status === 'dismissed') classes.push('dismissed')
  return classes
}

const getReportTypeClass = (type) => {
  const classes = {
    'inappropriate_content': 'content',
    'harassment': 'harassment',
    'fake_profile': 'fake',
    'spam': 'spam',
    'other': 'other'
  }
  return classes[type] || 'other'
}

const getReportTypeText = (type) => {
  const texts = {
    'inappropriate_content': 'Неподходящий контент',
    'harassment': 'Притеснение',
    'fake_profile': 'Фейковый профиль',
    'spam': 'Спам',
    'other': 'Другое'
  }
  return texts[type] || 'Неизвестно'
}

const getPriorityClass = (priority) => {
  switch (priority) {
    case 'high': return 'high'
    case 'medium': return 'medium'
    default: return 'low'
  }
}

const getPriorityText = (priority) => {
  switch (priority) {
    case 'high': return 'Высокий'
    case 'medium': return 'Средний'
    default: return 'Низкий'
  }
}

const getStatusClass = (status) => {
  switch (status) {
    case 'pending': return 'pending'
    case 'investigating': return 'investigating'
    case 'resolved': return 'resolved'
    case 'dismissed': return 'dismissed'
    default: return 'pending'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'pending': return 'Новая'
    case 'investigating': return 'В работе'
    case 'resolved': return 'Решена'
    case 'dismissed': return 'Отклонена'
    default: return 'Неизвестно'
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
  fetchReports()
}, { deep: true })

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.admin-reports {
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

.reports-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.report-card {
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-small);
  overflow: hidden;
  transition: transform 0.2s ease;
}

.report-card:hover {
  transform: translateY(-2px);
}

.report-card.high-priority {
  border-left: 4px solid var(--danger-color);
}

.report-card.resolved {
  opacity: 0.7;
  border-left: 4px solid var(--success-color);
}

.report-card.dismissed {
  opacity: 0.7;
  border-left: 4px solid var(--text-secondary);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.report-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.report-id {
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.report-type {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.report-type.content {
  background-color: var(--warning-color);
  color: white;
}

.report-type.harassment {
  background-color: var(--danger-color);
  color: white;
}

.report-type.fake {
  background-color: var(--info-color);
  color: white;
}

.report-type.spam {
  background-color: var(--text-secondary);
  color: white;
}

.report-type.other {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.report-priority {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.report-priority.high {
  background-color: var(--danger-color);
  color: white;
}

.report-priority.medium {
  background-color: var(--warning-color);
  color: white;
}

.report-priority.low {
  background-color: var(--success-color);
  color: white;
}

.report-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
}

.report-status.pending {
  background-color: var(--warning-color);
  color: white;
}

.report-status.investigating {
  background-color: var(--info-color);
  color: white;
}

.report-status.resolved {
  background-color: var(--success-color);
  color: white;
}

.report-status.dismissed {
  background-color: var(--text-secondary);
  color: white;
}

.report-content {
  padding: var(--spacing-lg);
}

.reporter-info,
.reported-info {
  margin-bottom: var(--spacing-lg);
}

.user-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.user-avatar {
  width: 50px;
  height: 50px;
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

.report-date {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.report-reason {
  margin-bottom: var(--spacing-lg);
}

.report-reason h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.report-reason p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.report-evidence {
  margin-bottom: var(--spacing-lg);
}

.report-evidence h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.screenshots {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.screenshot {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.screenshot:hover {
  transform: scale(1.05);
}

.message-content {
  padding: var(--spacing-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.report-notes {
  margin-bottom: var(--spacing-lg);
}

.report-notes h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.report-notes p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.report-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
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
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.screenshot-viewer {
  max-width: 800px;
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

.screenshot-image {
  max-width: 100%;
  border-radius: var(--border-radius);
}

.form-group {
  margin-bottom: var(--spacing-lg);
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
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}
</style>
