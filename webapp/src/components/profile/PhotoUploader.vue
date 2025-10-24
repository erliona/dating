<template>
  <div class="photo-uploader">
    <div class="uploader-header">
      <h3>Фотографии</h3>
      <p>Добавьте ровно 3 фотографии</p>
    </div>

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
          <div v-if="photo.safe_score !== null" class="nsfw-indicator" :class="getNsfwClass(photo.safe_score)">
            {{ getNsfwText(photo.safe_score) }}
          </div>
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

    <div class="upload-tips">
      <h4>Советы для лучших фото:</h4>
      <ul>
        <li>Используйте качественные, четкие фотографии</li>
        <li>Покажите свое лицо на первом фото</li>
        <li>Добавьте фото в полный рост</li>
        <li>Избегайте групповых фото</li>
        <li>Не используйте фильтры или маски</li>
      </ul>
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
import { usePhotoUpload } from '../../composables/usePhotoUpload'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [null, null, null]
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'upload-complete', 'upload-error'])

const { uploadPhoto, compressImage } = usePhotoUpload()

const fileInput = ref(null)
const photos = ref([...props.modelValue])
const uploading = ref([false, false, false])
const uploadProgress = ref([0, 0, 0])
const currentPhotoIndex = ref(0)

const isComplete = computed(() => {
  return photos.value.every(photo => photo !== null)
})

const addPhoto = (index) => {
  if (props.disabled) return
  currentPhotoIndex.value = index
  fileInput.value.click()
}

const removePhoto = (index) => {
  if (props.disabled) return
  photos.value[index] = null
  uploadProgress.value[index] = 0
  emit('update:modelValue', photos.value)
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const index = currentPhotoIndex.value
  
  // Validate file
  if (!validateFile(file)) return

  // Start upload
  uploading.value[index] = true
  uploadProgress.value[index] = 0

  try {
    // Compress image on client side
    const compressedFile = await compressImage(file, {
      maxWidth: 1920,
      maxHeight: 1920,
      quality: 0.85,
      maxSize: 2 * 1024 * 1024 // 2MB
    })

    // Upload to server
    const photoData = await uploadPhoto(compressedFile, (progress) => {
      uploadProgress.value[index] = progress
    })

    // Add photo to the slot
    photos.value[index] = {
      id: photoData.id,
      url: photoData.url,
      safe_score: photoData.safe_score,
      file_size: photoData.file_size,
      width: photoData.width,
      height: photoData.height
    }

    emit('update:modelValue', photos.value)
    emit('upload-complete', { index, photo: photos.value[index] })
  } catch (error) {
    // Handle error
    emit('upload-error', { index, error })
  } finally {
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

const getNsfwClass = (safeScore) => {
  if (safeScore === null) return ''
  if (safeScore > 0.8) return 'safe'
  if (safeScore > 0.5) return 'warning'
  return 'unsafe'
}

const getNsfwText = (safeScore) => {
  if (safeScore === null) return ''
  if (safeScore > 0.8) return '✓ Безопасно'
  if (safeScore > 0.5) return '⚠️ Проверяется'
  return '❌ Неподходящий контент'
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  photos.value = [...newValue]
}, { deep: true })
</script>

<style scoped>
.photo-uploader {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.uploader-header {
  text-align: center;
}

.uploader-header h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.uploader-header p {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0;
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
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.nsfw-indicator {
  position: absolute;
  bottom: var(--spacing-xs);
  left: var(--spacing-xs);
  right: var(--spacing-xs);
  padding: var(--spacing-xs);
  border-radius: var(--border-radius);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-align: center;
}

.nsfw-indicator.safe {
  background-color: rgba(var(--success-rgb), 0.9);
  color: white;
}

.nsfw-indicator.warning {
  background-color: rgba(var(--warning-rgb), 0.9);
  color: white;
}

.nsfw-indicator.unsafe {
  background-color: rgba(var(--danger-rgb), 0.9);
  color: white;
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

.upload-tips {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
}

.upload-tips h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.upload-tips ul {
  margin: 0;
  padding-left: var(--spacing-md);
}

.upload-tips li {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.upload-tips li:last-child {
  margin-bottom: 0;
}
</style>
