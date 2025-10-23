<template>
  <div class="step-photos">
    <div class="step-header">
      <h2>Добавьте фотографии</h2>
      <p>Добавьте ровно 3 фотографии для лучших совпадений</p>
    </div>

    <div class="step-content">
      <div class="photos-grid">
        <div 
          v-for="(photo, index) in photos" 
          :key="index"
          class="photo-slot"
          :class="{ 'empty': !photo, 'uploading': uploading[index] }"
        >
          <div v-if="photo" class="photo-preview">
            <img :src="photo.url" :alt="`Photo ${index + 1}`" />
            <button class="remove-photo" @click="removePhoto(index)">
              ✕
            </button>
          </div>
          <div v-else class="add-photo" @click="addPhoto(index)">
            <div class="add-photo-content">
              <span class="add-icon">📷</span>
              <span class="add-text">Добавить фото</span>
            </div>
          </div>
          <div v-if="uploading[index]" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress[index] + '%' }"></div>
            </div>
            <span class="progress-text">{{ uploadProgress[index] }}%</span>
          </div>
        </div>
      </div>

      <div class="photo-tips">
        <h4>Советы для лучших фото:</h4>
        <ul>
          <li>Используйте качественные, четкие фотографии</li>
          <li>Покажите свое лицо на первом фото</li>
          <li>Добавьте фото в полный рост</li>
          <li>Избегайте групповых фото</li>
          <li>Не используйте фильтры или маски</li>
        </ul>
      </div>
    </div>

    <div class="step-actions">
      <Button 
        variant="outline" 
        size="lg" 
        @click="handleBack"
        fullWidth
      >
        Назад
      </Button>
      <Button 
        variant="primary" 
        size="lg" 
        :disabled="!isValid"
        @click="handleNext"
        fullWidth
      >
        Продолжить
      </Button>
    </div>

    <!-- Hidden file input -->
    <input 
      ref="fileInput"
      type="file" 
      accept="image/*" 
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Button from '../common/Button.vue'

const emit = defineEmits(['next', 'back', 'update-data'])

const fileInput = ref(null)
const photos = ref([null, null, null])
const uploading = ref([false, false, false])
const uploadProgress = ref([0, 0, 0])
const currentPhotoIndex = ref(0)

const isValid = computed(() => {
  return photos.value.every(photo => photo !== null)
})

const addPhoto = (index) => {
  currentPhotoIndex.value = index
  fileInput.value.click()
}

const removePhoto = (index) => {
  photos.value[index] = null
  uploadProgress.value[index] = 0
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const index = currentPhotoIndex.value
  
  // Validate file
  if (!validateFile(file)) return

  // Start upload simulation
  uploading.value[index] = true
  uploadProgress.value[index] = 0

  try {
    // Simulate upload progress
    const progressInterval = setInterval(() => {
      if (uploadProgress.value[index] < 90) {
        uploadProgress.value[index] += 10
      }
    }, 100)

    // TODO: Implement actual photo upload to server
    const photoUrl = URL.createObjectURL(file)
    
    // Simulate server processing time
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    clearInterval(progressInterval)
    uploadProgress.value[index] = 100

    // Add photo to the slot
    photos.value[index] = {
      url: photoUrl,
      id: Date.now() + index, // Temporary ID
      file: file
    }

    uploading.value[index] = false
  } catch (error) {
    console.error('Failed to upload photo:', error)
    uploading.value[index] = false
    uploadProgress.value[index] = 0
  }

  // Reset file input
  event.target.value = ''
}

const validateFile = (file) => {
  // Check file type
  if (!file.type.startsWith('image/')) {
    alert('Пожалуйста, выберите изображение')
    return false
  }

  // Check file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('Размер файла не должен превышать 5MB')
    return false
  }

  return true
}

const handleNext = () => {
  if (isValid.value) {
    emit('update-data', { photos: photos.value })
    emit('next')
  }
}

const handleBack = () => {
  emit('back')
}

// Watch for changes and emit updates
watch(photos, (newPhotos) => {
  emit('update-data', { photos: newPhotos })
}, { deep: true })
</script>

<style scoped>
.step-photos {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--spacing-lg);
}

.step-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.step-header h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.step-header p {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0;
}

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.photo-slot {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: var(--border-radius);
  overflow: hidden;
  border: 2px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.photo-slot.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.photo-slot.empty:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.photo-preview {
  position: relative;
  width: 100%;
  height: 100%;
}

.photo-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-photo {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.add-photo-content {
  text-align: center;
  color: var(--text-secondary);
}

.add-icon {
  display: block;
  font-size: var(--font-size-2xl);
  margin-bottom: var(--spacing-xs);
}

.add-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.upload-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.progress-bar {
  width: 100%;
  height: 4px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: var(--font-size-xs);
  text-align: center;
}

.photo-tips {
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius);
}

.photo-tips h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.photo-tips ul {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.photo-tips li {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.photo-tips li:last-child {
  margin-bottom: 0;
}

.step-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

.step-actions .btn {
  flex: 1;
}
</style>