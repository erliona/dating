<template>
  <div class="step-interests">
    <div class="step-header">
      <h2>Ваши интересы</h2>
      <p>Выберите до 10 интересов, которые вас описывают</p>
    </div>

    <div class="step-content">
      <div class="interests-grid">
        <label 
          v-for="interest in interestOptions" 
          :key="interest.value"
          class="interest-option"
          :class="{ 
            'selected': formData.interests?.includes(interest.value),
            'disabled': formData.interests?.length >= 10 && !formData.interests?.includes(interest.value)
          }"
        >
          <input 
            v-model="formData.interests" 
            type="checkbox" 
            :value="interest.value"
            :disabled="formData.interests?.length >= 10 && !formData.interests?.includes(interest.value)"
          />
          <span class="interest-icon">{{ interest.icon }}</span>
          <span class="interest-label">{{ interest.label }}</span>
        </label>
      </div>

      <div class="selection-info">
        <p class="selection-count">
          Выбрано: {{ formData.interests?.length || 0 }}/10
        </p>
        <p v-if="formData.interests?.length < 5" class="selection-hint">
          💡 Добавьте больше интересов для лучших совпадений
        </p>
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
        @click="handleNext"
        :disabled="!isValid"
        fullWidth
      >
        Продолжить
      </Button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Button from '../common/Button.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'next', 'back'])

// Использовать computed для двусторонней привязки
const formData = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const interestOptions = [
  { value: 'music', label: 'Музыка', icon: '🎵' },
  { value: 'movies', label: 'Кино', icon: '🎬' },
  { value: 'books', label: 'Книги', icon: '📚' },
  { value: 'travel', label: 'Путешествия', icon: '✈️' },
  { value: 'sports', label: 'Спорт', icon: '⚽' },
  { value: 'fitness', label: 'Фитнес', icon: '💪' },
  { value: 'cooking', label: 'Кулинария', icon: '👨‍🍳' },
  { value: 'art', label: 'Искусство', icon: '🎨' },
  { value: 'photography', label: 'Фотография', icon: '📸' },
  { value: 'gaming', label: 'Игры', icon: '🎮' },
  { value: 'dancing', label: 'Танцы', icon: '💃' },
  { value: 'nature', label: 'Природа', icon: '🌿' },
  { value: 'animals', label: 'Животные', icon: '🐕' },
  { value: 'technology', label: 'Технологии', icon: '💻' },
  { value: 'fashion', label: 'Мода', icon: '👗' },
  { value: 'cars', label: 'Автомобили', icon: '🚗' },
  { value: 'yoga', label: 'Йога', icon: '🧘' },
  { value: 'reading', label: 'Чтение', icon: '📖' },
  { value: 'writing', label: 'Письмо', icon: '✍️' },
  { value: 'volunteering', label: 'Волонтерство', icon: '🤝' },
  { value: 'meditation', label: 'Медитация', icon: '🧘‍♀️' },
  { value: 'board_games', label: 'Настольные игры', icon: '🎲' },
  { value: 'hiking', label: 'Походы', icon: '🥾' },
  { value: 'swimming', label: 'Плавание', icon: '🏊' },
  { value: 'cycling', label: 'Велоспорт', icon: '🚴' },
  { value: 'running', label: 'Бег', icon: '🏃' },
  { value: 'painting', label: 'Живопись', icon: '🖌️' },
  { value: 'gardening', label: 'Садоводство', icon: '🌱' },
  { value: 'wine', label: 'Вино', icon: '🍷' },
  { value: 'coffee', label: 'Кофе', icon: '☕' }
]

const isValid = computed(() => {
  return formData.value.interests && formData.value.interests.length > 0
})

const handleNext = () => {
  if (isValid.value) {
    emit('next')
  }
}

const handleBack = () => {
  emit('back')
}
</script>

<style scoped>
.step-interests {
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
  gap: var(--spacing-lg);
}

.interests-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--spacing-md);
}

.interest-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: white;
}

.interest-option:hover:not(.disabled) {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.interest-option.selected {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.interest-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.interest-option input[type="checkbox"] {
  display: none;
}

.interest-icon {
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-xs);
}

.interest-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-align: center;
}

.selection-info {
  text-align: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.selection-count {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.selection-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.step-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.step-actions .btn {
  flex: 1;
}
</style>