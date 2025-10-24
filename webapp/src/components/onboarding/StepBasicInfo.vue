<template>
  <div class="step-basic-info">
    <div class="step-header">
      <h2>Основная информация</h2>
      <p>Расскажите немного о себе</p>
    </div>

    <div class="step-content">
      <div class="form-group">
        <Input
          v-model="formData.name"
          label="Имя"
          placeholder="Как вас зовут?"
          :required="true"
          :maxlength="50"
          :error="errors.name"
        />
      </div>

      <div class="form-group">
        <Input
          v-model="formData.birth_date"
          type="date"
          label="Дата рождения"
          :required="true"
          :max="maxDate"
          :error="errors.birth_date"
        />
        <p class="form-hint">Вам должно быть не менее 18 лет</p>
      </div>

      <div class="form-group">
        <label class="form-label">Пол *</label>
        <div class="radio-group">
          <label class="radio-option">
            <input 
              v-model="formData.gender" 
              type="radio" 
              value="male" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Мужской</span>
          </label>
          <label class="radio-option">
            <input 
              v-model="formData.gender" 
              type="radio" 
              value="female" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Женский</span>
          </label>
          <label class="radio-option">
            <input 
              v-model="formData.gender" 
              type="radio" 
              value="other" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Другой</span>
          </label>
        </div>
        <div v-if="errors.gender" class="error-message">{{ errors.gender }}</div>
      </div>

      <div class="form-group">
        <label class="form-label">Кого ищете *</label>
        <div class="radio-group">
          <label class="radio-option">
            <input 
              v-model="formData.orientation" 
              type="radio" 
              value="male" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Мужчин</span>
          </label>
          <label class="radio-option">
            <input 
              v-model="formData.orientation" 
              type="radio" 
              value="female" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Женщин</span>
          </label>
          <label class="radio-option">
            <input 
              v-model="formData.orientation" 
              type="radio" 
              value="any" 
            />
            <span class="radio-custom"></span>
            <span class="radio-label">Всех</span>
          </label>
        </div>
        <div v-if="errors.orientation" class="error-message">{{ errors.orientation }}</div>
      </div>
    </div>

    <div class="step-actions">
      <Button 
        variant="primary" 
        size="lg" 
        :disabled="!isValid"
        @click="handleNext"
        @mousedown="console.log('Button mousedown')"
        @mouseup="console.log('Button mouseup')"
        @touchstart="console.log('Button touchstart')"
        @touchend="console.log('Button touchend')"
        fullWidth
      >
        Продолжить ({{ isValid ? 'активна' : 'неактивна' }})
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Input from '../common/Input.vue'
import Button from '../common/Button.vue'

const emit = defineEmits(['next', 'update-data'])

const formData = ref({
  name: '',
  birth_date: '',
  gender: '',
  orientation: ''
})

const errors = ref({})

const maxDate = computed(() => {
  const today = new Date()
  const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate())
  return eighteenYearsAgo.toISOString().split('T')[0]
})

const isValid = computed(() => {
  return formData.value.name.trim().length >= 2 &&
         formData.value.birth_date &&
         formData.value.gender &&
         formData.value.orientation
})

const validateForm = () => {
  errors.value = {}

  if (!formData.value.name.trim()) {
    errors.value.name = 'Введите ваше имя'
  } else if (formData.value.name.trim().length < 2) {
    errors.value.name = 'Имя должно содержать минимум 2 символа'
  }

  if (!formData.value.birth_date) {
    errors.value.birth_date = 'Выберите дату рождения'
  } else {
    const birthDate = new Date(formData.value.birth_date)
    const today = new Date()
    const age = today.getFullYear() - birthDate.getFullYear()
    const monthDiff = today.getMonth() - birthDate.getMonth()
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      if (age - 1 < 18) {
        errors.value.birth_date = 'Вам должно быть не менее 18 лет'
      }
    } else if (age < 18) {
      errors.value.birth_date = 'Вам должно быть не менее 18 лет'
    }
  }

  if (!formData.value.gender) {
    errors.value.gender = 'Выберите ваш пол'
  }

  if (!formData.value.orientation) {
    errors.value.orientation = 'Выберите кого ищете'
  }

  return Object.keys(errors.value).length === 0
}

const handleNext = () => {
  console.log('🔥 handleNext called!')
  console.log('Form data:', formData.value)
  console.log('Is valid:', isValid.value)
  validateForm()
  console.log('Errors after validation:', errors.value)
  if (Object.keys(errors.value).length === 0) {
    console.log('✅ No errors, proceeding to next step')
    emit('update-data', formData.value)
    emit('next')
  } else {
    console.log('❌ Has errors, not proceeding')
  }
}

// Watch for changes and emit updates
watch(formData, (newData) => {
  emit('update-data', newData)
  // Clear errors when user starts typing
  if (Object.keys(errors.value).length > 0) {
    errors.value = {}
  }
}, { deep: true })
</script>

<style scoped>
.step-basic-info {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--spacing-md);
}

.step-header {
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.step-header h2 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--text-primary);
}

.step-header p {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.radio-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s ease;
}

.radio-option:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.radio-option input[type="radio"] {
  display: none;
}

.radio-custom {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  position: relative;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.radio-option input[type="radio"]:checked + .radio-custom {
  border-color: var(--primary-color);
  background-color: var(--primary-color);
}

.radio-option input[type="radio"]:checked + .radio-custom::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  background-color: white;
  border-radius: 50%;
}

.radio-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.form-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.error-message {
  font-size: var(--font-size-sm);
  color: var(--danger-color);
  margin-top: var(--spacing-xs);
}

.step-actions {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}
</style>