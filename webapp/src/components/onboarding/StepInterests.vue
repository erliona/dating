<template>
  <div class="step-interests">
    <div class="step-header">
      <h2>Ваши интересы</h2>
      <p>Выберите до 10 интересов (необязательно)</p>
    </div>

    <div class="step-content">
      <div class="interests-grid">
        <label 
          v-for="interest in interests" 
          :key="interest.value"
          class="interest-item"
          :class="{ 'selected': localData.interests.includes(interest.value) }"
        >
          <input
            v-model="localData.interests"
            type="checkbox"
            :value="interest.value"
            :disabled="!localData.interests.includes(interest.value) && localData.interests.length >= 10"
          />
          <span class="interest-label">
            <span class="interest-icon">{{ interest.icon }}</span>
            {{ interest.label }}
          </span>
        </label>
      </div>

      <div class="selection-info">
        Выбрано: {{ localData.interests.length }}/10
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const localData = ref({ ...props.modelValue })

const interests = [
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
  { value: 'wine', label: 'Вино', icon: '🍷' }
]

watch(localData, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })
</script>

<style scoped>
.step-interests {
  max-width: 400px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.step-header h2 {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.step-header p {
  color: var(--text-secondary);
  margin-bottom: 0;
}

.interests-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.interest-item {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.interest-item input[type="checkbox"] {
  display: none;
}

.interest-label {
  display: flex;
  align-items: center;
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-small);
  background-color: var(--bg-primary);
  transition: all var(--transition-fast);
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.interest-item.selected .interest-label {
  border-color: var(--primary-color);
  background-color: rgba(255, 107, 107, 0.05);
}

.interest-item:not(.selected) .interest-label:hover {
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.interest-item input[type="checkbox"]:disabled + .interest-label {
  opacity: 0.5;
  cursor: not-allowed;
}

.interest-icon {
  font-size: var(--font-size-md);
  margin-right: var(--spacing-sm);
}

.selection-info {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}
</style>
