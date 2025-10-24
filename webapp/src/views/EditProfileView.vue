<template>
  <div class="edit-profile-view tg-viewport tg-safe-area">
    <!-- Header -->
    <div class="edit-header">
      <button class="btn btn-icon" @click="$router.back()">
        ←
      </button>
      <h2>Редактировать профиль</h2>
      <button class="btn btn-primary" @click="saveProfile" :disabled="saving">
        {{ saving ? 'Сохранение...' : 'Сохранить' }}
      </button>
    </div>

    <!-- Content -->
    <div class="edit-content">
      <!-- Photos Section -->
      <div class="section">
        <h3>Фотографии</h3>
        <div class="photos-grid">
          <div 
            v-for="(photo, index) in photos" 
            :key="index"
            class="photo-slot"
            :class="{ 'empty': !photo }"
          >
            <img v-if="photo" :src="photo.url" :alt="`Photo ${index + 1}`" />
            <div v-else class="add-photo" @click="addPhoto(index)">
              <span class="add-icon">+</span>
            </div>
            <button 
              v-if="photo" 
              class="remove-photo" 
              @click="removePhoto(index)"
            >
              ✕
            </button>
          </div>
        </div>
        <p class="photo-hint">Добавьте ровно 3 фотографии</p>
      </div>

      <!-- Basic Info -->
      <div class="section">
        <h3>Основная информация</h3>
        <div class="form-group">
          <label>Имя *</label>
          <input 
            v-model="formData.name" 
            type="text" 
            placeholder="Ваше имя"
            maxlength="50"
          />
        </div>
        <div class="form-group">
          <label>Дата рождения *</label>
          <input 
            v-model="formData.birth_date" 
            type="date" 
            :max="maxDate"
          />
        </div>
        <div class="form-group">
          <label>Пол *</label>
          <div class="radio-group">
            <label class="radio-option">
              <input 
                v-model="formData.gender" 
                type="radio" 
                value="male" 
              />
              <span>Мужской</span>
            </label>
            <label class="radio-option">
              <input 
                v-model="formData.gender" 
                type="radio" 
                value="female" 
              />
              <span>Женский</span>
            </label>
            <label class="radio-option">
              <input 
                v-model="formData.gender" 
                type="radio" 
                value="other" 
              />
              <span>Другой</span>
            </label>
          </div>
        </div>
        <div class="form-group">
          <label>Ориентация *</label>
          <div class="radio-group">
            <label class="radio-option">
              <input 
                v-model="formData.orientation" 
                type="radio" 
                value="male" 
              />
              <span>Мужчины</span>
            </label>
            <label class="radio-option">
              <input 
                v-model="formData.orientation" 
                type="radio" 
                value="female" 
              />
              <span>Женщины</span>
            </label>
            <label class="radio-option">
              <input 
                v-model="formData.orientation" 
                type="radio" 
                value="any" 
              />
              <span>Все</span>
            </label>
          </div>
        </div>
      </div>

      <!-- About -->
      <div class="section">
        <h3>О себе</h3>
        <div class="form-group">
          <label>Био</label>
          <textarea 
            v-model="formData.bio" 
            placeholder="Расскажите о себе..."
            maxlength="500"
            rows="4"
          ></textarea>
          <div class="char-count">{{ formData.bio?.length || 0 }}/500</div>
        </div>
        <div class="form-group">
          <label>Цель знакомства</label>
          <div class="checkbox-group">
            <label v-for="goal in goalOptions" :key="goal.value" class="checkbox-option">
              <input 
                v-model="formData.goal" 
                type="checkbox" 
                :value="goal.value"
              />
              <span>{{ goal.label }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Interests -->
      <div class="section">
        <h3>Интересы</h3>
        <div class="interests-grid">
          <label 
            v-for="interest in interestOptions" 
            :key="interest"
            class="interest-option"
            :class="{ 'selected': formData.interests?.includes(interest) }"
          >
            <input 
              v-model="formData.interests" 
              type="checkbox" 
              :value="interest"
              :disabled="formData.interests?.length >= 10 && !formData.interests?.includes(interest)"
            />
            <span>{{ interest }}</span>
          </label>
        </div>
        <p class="interests-hint">
          Выбрано: {{ formData.interests?.length || 0 }}/10
        </p>
      </div>

      <!-- Additional Info -->
      <div class="section">
        <h3>Дополнительно</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Рост (см)</label>
            <input 
              v-model.number="formData.height_cm" 
              type="number" 
              placeholder="170"
              min="120"
              max="220"
            />
          </div>
          <div class="form-group">
            <label>Образование</label>
            <select v-model="formData.education">
              <option value="">Выберите</option>
              <option value="school">Среднее</option>
              <option value="college">Среднее специальное</option>
              <option value="university">Высшее</option>
              <option value="postgraduate">Аспирантура</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Профессия</label>
          <input 
            v-model="formData.profession" 
            type="text" 
            placeholder="Ваша профессия"
          />
        </div>
        <div class="form-group">
          <label>Языки</label>
          <input 
            v-model="formData.languages" 
            type="text" 
            placeholder="Русский, English"
          />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Дети</label>
            <select v-model="formData.has_children">
              <option value="">Не указано</option>
              <option :value="true">Есть</option>
              <option :value="false">Нет</option>
            </select>
          </div>
          <div class="form-group">
            <label>Хочу детей</label>
            <select v-model="formData.wants_children">
              <option value="">Не указано</option>
              <option :value="true">Да</option>
              <option :value="false">Нет</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Курение</label>
            <select v-model="formData.smoking">
              <option value="">Не указано</option>
              <option value="never">Никогда</option>
              <option value="occasionally">Иногда</option>
              <option value="regularly">Регулярно</option>
              <option value="quit">Бросил(а)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Алкоголь</label>
            <select v-model="formData.drinking">
              <option value="">Не указано</option>
              <option value="never">Никогда</option>
              <option value="occasionally">Иногда</option>
              <option value="regularly">Регулярно</option>
              <option value="quit">Бросил(а)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Privacy Settings -->
      <div class="section">
        <h3>Настройки приватности</h3>
        <div class="privacy-options">
          <label class="privacy-option">
            <input 
              type="checkbox" 
              v-model="formData.hide_distance"
            />
            <span>Скрыть расстояние</span>
          </label>
          <label class="privacy-option">
            <input 
              type="checkbox" 
              v-model="formData.hide_age"
            />
            <span>Скрыть возраст</span>
          </label>
          <label class="privacy-option">
            <input 
              type="checkbox" 
              v-model="formData.hide_online"
            />
            <span>Скрыть статус онлайн</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Photo Upload Modal -->
    <div v-if="showPhotoModal" class="modal-overlay" @click="showPhotoModal = false">
      <div class="photo-modal" @click.stop>
        <div class="photo-modal-header">
          <h3>Добавить фото</h3>
          <button class="btn btn-icon" @click="showPhotoModal = false">
            ✕
          </button>
        </div>
        <div class="photo-modal-content">
          <input 
            ref="photoInput"
            type="file" 
            accept="image/*" 
            @change="handlePhotoUpload"
            style="display: none"
          />
          <button class="btn btn-primary" @click="$refs.photoInput.click()">
            Выбрать фото
          </button>
          <div v-if="uploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <p>Загрузка... {{ uploadProgress }}%</p>
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

const router = useRouter()
const userStore = useUserStore()
const { showAlert } = useTelegram()

const saving = ref(false)
const showPhotoModal = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const currentPhotoIndex = ref(0)

const formData = ref({
  name: '',
  birth_date: '',
  gender: '',
  orientation: '',
  bio: '',
  goal: [],
  interests: [],
  height_cm: null,
  education: '',
  profession: '',
  languages: '',
  has_children: null,
  wants_children: null,
  smoking: '',
  drinking: '',
  hide_distance: false,
  hide_age: false,
  hide_online: false
})

const photos = ref([null, null, null])

const maxDate = computed(() => {
  const today = new Date()
  const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate())
  return eighteenYearsAgo.toISOString().split('T')[0]
})

const goalOptions = [
  { value: 'serious', label: 'Серьезные отношения' },
  { value: 'dating', label: 'Свидания' },
  { value: 'casual', label: 'Несерьезные отношения' },
  { value: 'friendship', label: 'Дружба' }
]

const interestOptions = [
  'Спорт', 'Музыка', 'Кино', 'Путешествия', 'Книги', 'Искусство',
  'Фотография', 'Танцы', 'Кулинария', 'Природа', 'Технологии',
  'Мода', 'Животные', 'Игры', 'Йога', 'Бег', 'Велоспорт',
  'Горные лыжи', 'Сноуборд', 'Серфинг', 'Рок-музыка', 'Джаз',
  'Классическая музыка', 'Театр', 'Опера', 'Балет', 'Живопись',
  'Скульптура', 'Поэзия', 'Писательство', 'Блоггинг'
]

const loadProfile = () => {
  if (userStore.profile) {
    formData.value = {
      name: userStore.profile.name || '',
      birth_date: userStore.profile.birth_date || '',
      gender: userStore.profile.gender || '',
      orientation: userStore.profile.orientation || '',
      bio: userStore.profile.bio || '',
      goal: userStore.profile.goal || [],
      interests: userStore.profile.interests || [],
      height_cm: userStore.profile.height_cm || null,
      education: userStore.profile.education || '',
      profession: userStore.profile.profession || '',
      languages: userStore.profile.languages || '',
      has_children: userStore.profile.has_children,
      wants_children: userStore.profile.wants_children,
      smoking: userStore.profile.smoking || '',
      drinking: userStore.profile.drinking || '',
      hide_distance: userStore.profile.hide_distance || false,
      hide_age: userStore.profile.hide_age || false,
      hide_online: userStore.profile.hide_online || false
    }
    
    // Load photos
    if (userStore.profile.photos) {
      userStore.profile.photos.forEach((photo, index) => {
        if (index < 3) {
          photos.value[index] = photo
        }
      })
    }
  }
}

const saveProfile = async () => {
  saving.value = true
  try {
    await userStore.updateProfile(formData.value)
    showAlert('Профиль обновлен')
    router.back()
  } catch (error) {
    // Handle error
    showAlert('Не удалось сохранить профиль')
  } finally {
    saving.value = false
  }
}

const addPhoto = (index) => {
  currentPhotoIndex.value = index
  showPhotoModal.value = true
}

const removePhoto = (index) => {
  photos.value[index] = null
}

const handlePhotoUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    // Simulate upload progress
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 100)

    // TODO: Implement actual photo upload
    const photoUrl = URL.createObjectURL(file)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100

    // Add photo to the slot
    photos.value[currentPhotoIndex.value] = {
      url: photoUrl,
      id: Date.now() // Temporary ID
    }

    showPhotoModal.value = false
    showAlert('Фото загружено')
  } catch (error) {
    // Handle error
    showAlert('Не удалось загрузить фото')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

onMounted(() => {
  if (!userStore.profile) {
    userStore.fetchProfile().then(() => {
      loadProfile()
    })
  } else {
    loadProfile()
  }
})
</script>

<style scoped>
.edit-profile-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.edit-header h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.edit-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.section {
  margin-bottom: var(--spacing-md);
}

.section h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.photo-slot {
  position: relative;
  width: 100%;
  height: 120px;
  border-radius: var(--border-radius);
  overflow: hidden;
  border: 2px solid var(--border-color);
}

.photo-slot.empty {
  background-color: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.add-photo {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
}

.add-icon {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
}

.remove-photo {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.photo-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
  margin: 0;
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  background-color: white;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.char-count {
  text-align: right;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.radio-group,
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.radio-option,
.checkbox-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.radio-option input,
.checkbox-option input {
  width: auto;
  margin: 0;
}

.interests-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.interest-option {
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.interest-option:hover {
  border-color: var(--primary-color);
}

.interest-option.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.interest-option input {
  display: none;
}

.interests-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
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
  max-width: 400px;
  width: 100%;
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
  text-align: center;
}

.upload-progress {
  margin-top: var(--spacing-md);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.upload-progress p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}
</style>