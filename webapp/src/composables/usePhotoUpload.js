import { ref } from 'vue'
import { useApi } from './useApi'

export function usePhotoUpload() {
  const { api } = useApi()
  const uploading = ref(false)
  const progress = ref(0)
  const error = ref(null)

  const compressImage = (file, maxWidth = 1920, maxHeight = 1920, quality = 0.85) => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img
        
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height
            height = maxHeight
          }
        }

        canvas.width = width
        canvas.height = height

        // Draw and compress
        ctx.drawImage(img, 0, 0, width, height)
        
        canvas.toBlob(
          (blob) => resolve(blob),
          'image/jpeg',
          quality
        )
      }

      img.src = URL.createObjectURL(file)
    })
  }

  const validateImage = (file) => {
    const maxSize = 5 * 1024 * 1024 // 5MB
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']

    if (!allowedTypes.includes(file.type)) {
      throw new Error('Неподдерживаемый формат файла. Используйте JPG, PNG или WebP.')
    }

    if (file.size > maxSize) {
      throw new Error('Файл слишком большой. Максимальный размер: 5MB.')
    }

    return true
  }

  const uploadPhoto = async (file, userId) => {
    uploading.value = true
    progress.value = 0
    error.value = null

    try {
      // Validate file
      validateImage(file)

      // Compress image
      const compressedFile = await compressImage(file)
      
      // Create form data
      const formData = new FormData()
      formData.append('photo', compressedFile, file.name)
      formData.append('user_id', userId)

      // Upload with progress tracking
      const response = await api.post('/media/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          progress.value = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
        }
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || err.message || 'Ошибка загрузки фото'
      throw err
    } finally {
      uploading.value = false
      progress.value = 0
    }
  }

  const deletePhoto = async (photoId) => {
    try {
      await api.delete(`/media/${photoId}`)
      return true
    } catch (err) {
      error.value = err.response?.data?.error || 'Ошибка удаления фото'
      throw err
    }
  }

  return {
    uploading,
    progress,
    error,
    uploadPhoto,
    deletePhoto,
    compressImage,
    validateImage
  }
}
