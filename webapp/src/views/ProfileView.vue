<template>
  <div class="profile-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="profile-header">
      <button class="btn btn-icon" @click="$router.back()">
        ←
      </button>
      <h2>Мой профиль</h2>
      <button class="btn btn-icon" @click="editProfile">
        ✏️
      </button>
    </div>

    <!-- Profile Content -->
    <div class="profile-content">
      <!-- Photos Section -->
      <div class="photos-section">
        <div class="main-photo">
          <img 
            :src="getMainPhoto()" 
            :alt="userStore.profile?.name"
            @click="showPhotoModal = true"
          />
          <div v-if="userStore.profile?.is_verified" class="verification-badge">
            ✓
          </div>
        </div>
        <div class="photo-thumbnails">
          <div 
            v-for="(photo, index) in userStore.profile?.photos?.slice(1) || []" 
            :key="index"
            class="photo-thumbnail"
            @click="showPhotoModal = true"
          >
            <img :src="photo.url" :alt="`Photo ${index + 2}`" />
          </div>
          <div 
            v-if="(userStore.profile?.photos?.length || 0) < 3"
            class="photo-thumbnail add-photo"
            @click="addPhoto"
          >
            <div class="add-photo-content">
              <span class="add-photo-icon">+</span>
              <span class="add-photo-text">Добавить фото</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Basic Info -->
      <div class="info-section">
        <div class="info-header">
          <h3>{{ userStore.profile?.name }}, {{ getAge() }}</h3>
          <div v-if="userStore.profile?.is_verified" class="verified-badge">
            <span class="verified-icon">✓</span>
            <span>Верифицирован</span>
          </div>
        </div>
        <p v-if="userStore.profile?.bio" class="bio">
          {{ userStore.profile.bio }}
        </p>
        <div class="location">
          📍 {{ userStore.profile?.city }}, {{ userStore.profile?.country }}
        </div>
      </div>

      <!-- Profile Completion -->
      <div class="completion-section">
        <div class="completion-header">
          <h4>Завершенность профиля</h4>
          <span class="completion-percentage">{{ getCompletionPercentage() }}%</span>
        </div>
        <div class="completion-bar">
          <div 
            class="completion-fill" 
            :style="{ width: getCompletionPercentage() + '%' }"
          ></div>
        </div>
        <div class="completion-tips">
          <p v-if="getCompletionPercentage() < 100">
            Добавьте недостающую информацию для лучших совпадений
          </p>
        </div>
      </div>

      <!-- Details -->
      <div class="details-section">
        <h4>Детали</h4>
        <div class="details-grid">
          <div v-if="userStore.profile?.goal" class="detail-item">
            <span class="detail-label">Цель:</span>
            <span class="detail-value">{{ getGoalText() }}</span>
          </div>
          <div v-if="userStore.profile?.education" class="detail-item">
            <span class="detail-label">Образование:</span>
            <span class="detail-value">{{ userStore.profile.education }}</span>
          </div>
          <div v-if="userStore.profile?.profession" class="detail-item">
            <span class="detail-label">Профессия:</span>
            <span class="detail-value">{{ userStore.profile.profession }}</span>
          </div>
          <div v-if="userStore.profile?.height_cm" class="detail-item">
            <span class="detail-label">Рост:</span>
            <span class="detail-value">{{ userStore.profile.height_cm }} см</span>
          </div>
          <div v-if="userStore.profile?.has_children !== null" class="detail-item">
            <span class="detail-label">Дети:</span>
            <span class="detail-value">{{ getChildrenText() }}</span>
          </div>
          <div v-if="userStore.profile?.smoking !== null" class="detail-item">
            <span class="detail-label">Курение:</span>
            <span class="detail-value">{{ getSmokingText() }}</span>
          </div>
          <div v-if="userStore.profile?.drinking !== null" class="detail-item">
            <span class="detail-label">Алкоголь:</span>
            <span class="detail-value">{{ getDrinkingText() }}</span>
          </div>
        </div>
      </div>

      <!-- Interests -->
      <div v-if="userStore.profile?.interests?.length" class="interests-section">
        <h4>Интересы</h4>
        <div class="interests-list">
          <span 
            v-for="interest in userStore.profile.interests" 
            :key="interest"
            class="interest-tag"
          >
            {{ interest }}
          </span>
        </div>
      </div>

      <!-- Languages -->
      <div v-if="userStore.profile?.languages?.length" class="languages-section">
        <h4>Языки</h4>
        <div class="languages-list">
          <span 
            v-for="language in userStore.profile.languages" 
            :key="language"
            class="language-tag"
          >
            {{ language }}
          </span>
        </div>
      </div>

      <!-- Privacy Settings -->
      <div class="privacy-section">
        <h4>Настройки приватности</h4>
        <div class="privacy-options">
          <label class="privacy-option">
            <input 
              type="checkbox" 
              :checked="userStore.profile?.hide_distance"
              @change="updatePrivacy('hide_distance', $event.target.checked)"
            />
            <span>Скрыть расстояние</span>
          </label>
          <label class="privacy-option">
            <input 
              type="checkbox" 
              :checked="userStore.profile?.hide_age"
              @change="updatePrivacy('hide_age', $event.target.checked)"
            />
            <span>Скрыть возраст</span>
          </label>
          <label class="privacy-option">
            <input 
              type="checkbox" 
              :checked="userStore.profile?.hide_online"
              @change="updatePrivacy('hide_online', $event.target.checked)"
            />
            <span>Скрыть статус онлайн</span>
          </label>
        </div>
      </div>

      <!-- Verification Flow -->
      <div class="verification-section">
        <VerificationFlow :verification-data="userStore.profile?.verification_data || {}" />
      </div>
    </div>

    <!-- Photo Modal -->
    <div v-if="showPhotoModal" class="modal-overlay" @click="showPhotoModal = false">
      <div class="photo-modal" @click.stop>
        <div class="photo-modal-header">
          <h3>Фотографии</h3>
          <button class="btn btn-icon" @click="showPhotoModal = false">
            ✕
          </button>
        </div>
        <div class="photo-modal-content">
          <div 
            v-for="(photo, index) in userStore.profile?.photos || []" 
            :key="index"
            class="modal-photo"
          >
            <img :src="photo.url" :alt="`Photo ${index + 1}`" />
          </div>
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
import VerificationFlow from '../components/profile/VerificationFlow.vue'

const router = useRouter()
const userStore = useUserStore()
const { showAlert } = useTelegram()

const showPhotoModal = ref(false)

const getMainPhoto = () => {
  return userStore.profile?.photos?.[0]?.url || '/default-avatar.png'
}

const getAge = () => {
  if (!userStore.profile?.birth_date) return ''
  
  const today = new Date()
  const birthDate = new Date(userStore.profile.birth_date)
  let age = today.getFullYear() - birthDate.getFullYear()
  const monthDiff = today.getMonth() - birthDate.getMonth()
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--
  }
  
  return age
}

const getCompletionPercentage = () => {
  if (!userStore.profile) return 0
  
  const fields = [
    'name', 'birth_date', 'gender', 'orientation', 'goal', 'bio',
    'interests', 'height_cm', 'education', 'profession', 'languages'
  ]
  
  const completedFields = fields.filter(field => {
    const value = userStore.profile[field]
    return value !== null && value !== undefined && value !== ''
  }).length
  
  const photoCount = userStore.profile.photos?.length || 0
  const photoScore = Math.min(photoCount, 3) / 3
  
  return Math.round(((completedFields + photoScore) / (fields.length + 1)) * 100)
}

const getGoalText = () => {
  const goals = {
    'dating': 'Серьезные отношения',
    'friendship': 'Дружба',
    'casual': 'Несерьезные отношения',
    'marriage': 'Брак'
  }
  return goals[userStore.profile?.goal] || userStore.profile?.goal
}

const getChildrenText = () => {
  if (userStore.profile?.has_children === true) {
    return userStore.profile?.wants_children ? 'Есть, хочу еще' : 'Есть'
  } else if (userStore.profile?.has_children === false) {
    return userStore.profile?.wants_children ? 'Нет, но хочу' : 'Нет'
  }
  return 'Не указано'
}

const getSmokingText = () => {
  const smoking = {
    'never': 'Никогда',
    'occasionally': 'Иногда',
    'regularly': 'Регулярно',
    'quit': 'Бросил(а)'
  }
  return smoking[userStore.profile?.smoking] || 'Не указано'
}

const getDrinkingText = () => {
  const drinking = {
    'never': 'Никогда',
    'occasionally': 'Иногда',
    'regularly': 'Регулярно',
    'quit': 'Бросил(а)'
  }
  return drinking[userStore.profile?.drinking] || 'Не указано'
}

const editProfile = () => {
  router.push('/profile/edit')
}

const addPhoto = () => {
  router.push('/profile/edit?step=photos')
}

const updatePrivacy = async (field, value) => {
  try {
    await userStore.updateProfile({ [field]: value })
    showAlert('Настройки обновлены')
  } catch (error) {
    // Handle error
    showAlert('Не удалось обновить настройки')
  }
}

onMounted(() => {
  if (!userStore.profile) {
    userStore.fetchProfile()
  }
})
</script>

<style scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.profile-header h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.profile-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.photos-section {
  margin-bottom: var(--spacing-md);
}

.main-photo {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: var(--border-radius);
  overflow: hidden;
  margin-bottom: var(--spacing-md);
  cursor: pointer;
}

.main-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.verification-badge {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  background-color: var(--primary-color);
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-bold);
}

.photo-thumbnails {
  display: flex;
  gap: var(--spacing-sm);
}

.photo-thumbnail {
  width: 80px;
  height: 80px;
  border-radius: var(--border-radius);
  overflow: hidden;
  cursor: pointer;
  border: 2px solid var(--border-color);
}

.photo-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.add-photo {
  background-color: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-photo-content {
  text-align: center;
  color: var(--text-secondary);
}

.add-photo-icon {
  display: block;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
}

.add-photo-text {
  font-size: var(--font-size-xs);
}

.info-section {
  margin-bottom: var(--spacing-md);
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.info-header h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.verified-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  background-color: var(--primary-color);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.verified-icon {
  font-weight: var(--font-weight-bold);
}

.bio {
  font-size: var(--font-size-md);
  line-height: 1.5;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.location {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.completion-section {
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.completion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.completion-header h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.completion-percentage {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  color: var(--primary-color);
}

.completion-bar {
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.completion-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.completion-tips p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.details-section,
.interests-section,
.languages-section,
.privacy-section {
  margin-bottom: var(--spacing-md);
}

.details-section h4,
.interests-section h4,
.languages-section h4,
.privacy-section h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
}

.detail-value {
  color: var(--text-primary);
  text-align: right;
}

.interests-list,
.languages-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.interest-tag,
.language-tag {
  background-color: var(--primary-color);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
}

.privacy-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.privacy-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.privacy-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
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

.photo-modal {
  background-color: white;
  border-radius: var(--border-radius);
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-large);
}

.photo-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.photo-modal-header h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.photo-modal-content {
  padding: var(--spacing-md);
  max-height: 60vh;
  overflow-y: auto;
}

.modal-photo {
  margin-bottom: var(--spacing-md);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.modal-photo:last-child {
  margin-bottom: 0;
}

.modal-photo img {
  width: 100%;
  height: auto;
  object-fit: cover;
}
</style>