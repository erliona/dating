<template>
  <div class="settings-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="settings-header">
      <button class="btn btn-icon" @click="$router.back()">
        ←
      </button>
      <h2>Настройки</h2>
      <div></div>
    </div>

    <!-- Content -->
    <div class="settings-content">
      <!-- Search Preferences -->
      <div class="settings-section">
        <h3>Поиск</h3>
        <div class="settings-group">
          <div class="setting-item">
            <div class="setting-info">
              <h4>Возраст</h4>
              <p>От {{ searchPreferences.min_age }} до {{ searchPreferences.max_age }} лет</p>
            </div>
            <button class="btn btn-outline" @click="showAgeModal = true">
              Изменить
            </button>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Расстояние</h4>
              <p>До {{ searchPreferences.max_distance_km }} км</p>
            </div>
            <button class="btn btn-outline" @click="showDistanceModal = true">
              Изменить
            </button>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Пол</h4>
              <p>{{ getGenderPreferenceText() }}</p>
            </div>
            <button class="btn btn-outline" @click="showGenderModal = true">
              Изменить
            </button>
          </div>
        </div>
      </div>

      <!-- Notifications -->
      <div class="settings-section">
        <h3>Уведомления</h3>
        <div class="settings-group">
          <div class="setting-item">
            <div class="setting-info">
              <h4>Новые матчи</h4>
              <p>Получать уведомления о новых совпадениях</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="notificationSettings.new_matches"
                @change="updateNotificationSettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Новые сообщения</h4>
              <p>Получать уведомления о новых сообщениях</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="notificationSettings.new_messages"
                @change="updateNotificationSettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Верификация</h4>
              <p>Получать уведомления о статусе верификации</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="notificationSettings.verification"
                @change="updateNotificationSettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <!-- Privacy -->
      <div class="settings-section">
        <h3>Приватность</h3>
        <div class="settings-group">
          <div class="setting-item">
            <div class="setting-info">
              <h4>Скрыть расстояние</h4>
              <p>Показывать "Рядом" вместо точного расстояния</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="privacySettings.hide_distance"
                @change="updatePrivacySettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Скрыть возраст</h4>
              <p>Не показывать свой возраст другим пользователям</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="privacySettings.hide_age"
                @change="updatePrivacySettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Скрыть статус онлайн</h4>
              <p>Не показывать когда вы в сети</p>
            </div>
            <label class="toggle">
              <input 
                type="checkbox" 
                v-model="privacySettings.hide_online"
                @change="updatePrivacySettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <!-- Account -->
      <div class="settings-section">
        <h3>Аккаунт</h3>
        <div class="settings-group">
          <div class="setting-item">
            <div class="setting-info">
              <h4>Верификация</h4>
              <p v-if="userStore.profile?.is_verified" class="verified-status">
                ✓ Профиль верифицирован
              </p>
              <p v-else class="unverified-status">
                Профиль не верифицирован
              </p>
            </div>
            <button 
              v-if="!userStore.profile?.is_verified"
              class="btn btn-primary" 
              @click="requestVerification"
            >
              Запросить
            </button>
          </div>
          
          <div class="setting-item">
            <div class="setting-info">
              <h4>Удалить аккаунт</h4>
              <p>Безвозвратно удалить профиль и все данные</p>
            </div>
            <button class="btn btn-danger" @click="showDeleteModal = true">
              Удалить
            </button>
          </div>
        </div>
      </div>

      <!-- Logout -->
      <div class="settings-section">
        <button class="btn btn-outline logout-btn" @click="logout">
          Выйти из аккаунта
        </button>
      </div>
    </div>

    <!-- Age Modal -->
    <div v-if="showAgeModal" class="modal-overlay" @click="showAgeModal = false">
      <div class="modal" @click.stop>
        <h3>Возрастные предпочтения</h3>
        <div class="age-range">
          <div class="range-input">
            <label>От {{ searchPreferences.min_age }} лет</label>
            <input 
              type="range" 
              v-model.number="searchPreferences.min_age"
              min="18" 
              max="65"
            />
          </div>
          <div class="range-input">
            <label>До {{ searchPreferences.max_age }} лет</label>
            <input 
              type="range" 
              v-model.number="searchPreferences.max_age"
              min="18" 
              max="65"
            />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showAgeModal = false">
            Отмена
          </button>
          <button class="btn btn-primary" @click="saveAgePreferences">
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Distance Modal -->
    <div v-if="showDistanceModal" class="modal-overlay" @click="showDistanceModal = false">
      <div class="modal" @click.stop>
        <h3>Расстояние поиска</h3>
        <div class="distance-input">
          <label>До {{ searchPreferences.max_distance_km }} км</label>
          <input 
            type="range" 
            v-model.number="searchPreferences.max_distance_km"
            min="1" 
            max="100"
          />
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showDistanceModal = false">
            Отмена
          </button>
          <button class="btn btn-primary" @click="saveDistancePreferences">
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Gender Modal -->
    <div v-if="showGenderModal" class="modal-overlay" @click="showGenderModal = false">
      <div class="modal" @click.stop>
        <h3>Кого ищете</h3>
        <div class="gender-options">
          <label class="gender-option">
            <input 
              type="radio" 
              v-model="searchPreferences.preferred_gender" 
              value="male"
            />
            <span>Мужчин</span>
          </label>
          <label class="gender-option">
            <input 
              type="radio" 
              v-model="searchPreferences.preferred_gender" 
              value="female"
            />
            <span>Женщин</span>
          </label>
          <label class="gender-option">
            <input 
              type="radio" 
              v-model="searchPreferences.preferred_gender" 
              value="any"
            />
            <span>Всех</span>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showGenderModal = false">
            Отмена
          </button>
          <button class="btn btn-primary" @click="saveGenderPreferences">
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Account Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="modal" @click.stop>
        <h3>Удалить аккаунт</h3>
        <p>Это действие нельзя отменить. Все ваши данные будут удалены навсегда.</p>
        <div class="delete-confirmation">
          <label>
            <input 
              type="checkbox" 
              v-model="deleteConfirmed"
            />
            Я понимаю, что это действие необратимо
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showDeleteModal = false">
            Отмена
          </button>
          <button 
            class="btn btn-danger" 
            @click="deleteAccount"
            :disabled="!deleteConfirmed"
          >
            Удалить аккаунт
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useTelegram } from '../composables/useTelegram'

const router = useRouter()
const userStore = useUserStore()
const { showAlert, closeApp } = useTelegram()

const showAgeModal = ref(false)
const showDistanceModal = ref(false)
const showGenderModal = ref(false)
const showDeleteModal = ref(false)
const deleteConfirmed = ref(false)

const searchPreferences = ref({
  min_age: 18,
  max_age: 35,
  max_distance_km: 25,
  preferred_gender: 'any'
})

const notificationSettings = ref({
  new_matches: true,
  new_messages: true,
  verification: true
})

const privacySettings = ref({
  hide_distance: false,
  hide_age: false,
  hide_online: false
})

const getGenderPreferenceText = () => {
  const genderMap = {
    'male': 'Мужчин',
    'female': 'Женщин',
    'any': 'Всех'
  }
  return genderMap[searchPreferences.value.preferred_gender] || 'Всех'
}

const loadSettings = async () => {
  try {
    // Load user preferences
    const preferences = await userStore.getUserPreferences()
    if (preferences) {
      searchPreferences.value = {
        min_age: preferences.min_age || 18,
        max_age: preferences.max_age || 35,
        max_distance_km: preferences.max_distance_km || 25,
        preferred_gender: preferences.preferred_gender || 'any'
      }
    }

    // Load notification settings
    const notifications = await userStore.getNotificationSettings()
    if (notifications) {
      notificationSettings.value = {
        new_matches: notifications.new_matches !== false,
        new_messages: notifications.new_messages !== false,
        verification: notifications.verification !== false
      }
    }

    // Load privacy settings from profile
    if (userStore.profile) {
      privacySettings.value = {
        hide_distance: userStore.profile.hide_distance || false,
        hide_age: userStore.profile.hide_age || false,
        hide_online: userStore.profile.hide_online || false
      }
    }
  } catch (error) {
    // Handle error
  }
}

const saveAgePreferences = async () => {
  try {
    await userStore.updateUserPreferences(searchPreferences.value)
    showAgeModal.value = false
    showAlert('Настройки сохранены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось сохранить настройки')
  }
}

const saveDistancePreferences = async () => {
  try {
    await userStore.updateUserPreferences(searchPreferences.value)
    showDistanceModal.value = false
    showAlert('Настройки сохранены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось сохранить настройки')
  }
}

const saveGenderPreferences = async () => {
  try {
    await userStore.updateUserPreferences(searchPreferences.value)
    showGenderModal.value = false
    showAlert('Настройки сохранены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось сохранить настройки')
  }
}

const updateNotificationSettings = async () => {
  try {
    await userStore.updateNotificationSettings(notificationSettings.value)
    showAlert('Настройки уведомлений обновлены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось обновить настройки')
  }
}

const updatePrivacySettings = async () => {
  try {
    await userStore.updateProfile(privacySettings.value)
    showAlert('Настройки приватности обновлены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось обновить настройки')
  }
}

const requestVerification = async () => {
  try {
    await userStore.requestVerification()
    showAlert('Запрос на верификацию отправлен')
  } catch (error) {
    // Handle error
    showAlert('Не удалось отправить запрос')
  }
}

const deleteAccount = async () => {
  if (!deleteConfirmed.value) return

  try {
    await userStore.deleteAccount()
    showAlert('Аккаунт удален')
    closeApp()
  } catch (error) {
    // Handle error
    showAlert('Не удалось удалить аккаунт')
  }
}

const logout = async () => {
  try {
    await userStore.logout()
    router.push('/')
  } catch (error) {
    // Handle error
    showAlert('Не удалось выйти из аккаунта')
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.settings-header h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.settings-section {
  margin-bottom: var(--spacing-md);
}

.settings-section h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.settings-group {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
}

.setting-info h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--text-primary);
}

.setting-info p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.verified-status {
  color: var(--success-color) !important;
}

.unverified-status {
  color: var(--text-secondary) !important;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 16px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle input:checked + .toggle-slider {
  background-color: var(--primary-color);
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(26px);
}

.logout-btn {
  width: 100%;
  padding: var(--spacing-md);
  font-size: var(--font-size-md);
  color: var(--danger-color);
  border-color: var(--danger-color);
}

.logout-btn:hover {
  background-color: var(--danger-color);
  color: white;
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
  padding: var(--spacing-md);
}

.modal {
  background-color: white;
  border-radius: var(--border-radius);
  max-width: 400px;
  width: 100%;
  box-shadow: var(--shadow-large);
  padding: var(--spacing-md);
}

.modal h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.modal p {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-md);
}

.age-range {
  margin-bottom: var(--spacing-md);
}

.range-input {
  margin-bottom: var(--spacing-md);
}

.range-input label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.range-input input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--border-color);
  outline: none;
  -webkit-appearance: none;
}

.range-input input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.distance-input {
  margin-bottom: var(--spacing-md);
}

.distance-input label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.gender-options {
  margin-bottom: var(--spacing-md);
}

.gender-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  cursor: pointer;
}

.gender-option input[type="radio"] {
  width: 18px;
  height: 18px;
}

.delete-confirmation {
  margin-bottom: var(--spacing-md);
}

.delete-confirmation label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.delete-confirmation input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.modal-actions .btn {
  min-width: 100px;
}
</style>