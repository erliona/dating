<template>
  <div class="step-additional">
    <div class="step-header">
      <h2>Дополнительно</h2>
      <p>Эти поля необязательны, но помогут найти лучших кандидатов</p>
    </div>

    <div class="step-content">
      <!-- Height -->
      <div class="form-group">
        <label class="form-label">Рост (см)</label>
        <input
          v-model="localData.height_cm"
          type="number"
          class="form-input"
          placeholder="Например: 175"
          min="120"
          max="220"
        />
      </div>

      <!-- Education -->
      <div class="form-group">
        <label class="form-label">Образование</label>
        <select v-model="localData.education" class="form-input form-select">
          <option value="">Выберите образование</option>
          <option value="secondary">Среднее</option>
          <option value="vocational">Среднее специальное</option>
          <option value="bachelor">Высшее (бакалавриат)</option>
          <option value="master">Высшее (магистратура)</option>
          <option value="phd">Ученая степень</option>
        </select>
      </div>

      <!-- Profession -->
      <div class="form-group">
        <label class="form-label">Профессия</label>
        <input
          v-model="localData.profession"
          type="text"
          class="form-input"
          placeholder="Например: Дизайнер"
          maxlength="100"
        />
      </div>

      <!-- Languages -->
      <div class="form-group">
        <label class="form-label">Языки</label>
        <div class="checkbox-group">
          <label class="checkbox-item" v-for="language in languages" :key="language.value">
            <input
              v-model="localData.languages"
              type="checkbox"
              :value="language.value"
            />
            <span class="checkbox-label">
              <span class="checkbox-icon">{{ language.icon }}</span>
              {{ language.label }}
            </span>
          </label>
        </div>
      </div>

      <!-- Children -->
      <div class="form-group">
        <label class="form-label">Дети</label>
        <div class="radio-group">
          <label class="radio-item" v-for="option in childrenOptions" :key="option.value">
            <input
              v-model="localData.has_children"
              type="radio"
              :value="option.value"
              name="has_children"
            />
            <span class="radio-label">
              <span class="radio-icon">{{ option.icon }}</span>
              {{ option.label }}
            </span>
          </label>
        </div>
      </div>

      <!-- Wants Children -->
      <div class="form-group">
        <label class="form-label">Хотите детей?</label>
        <div class="radio-group">
          <label class="radio-item" v-for="option in wantsChildrenOptions" :key="option.value">
            <input
              v-model="localData.wants_children"
              type="radio"
              :value="option.value"
              name="wants_children"
            />
            <span class="radio-label">
              <span class="radio-icon">{{ option.icon }}</span>
              {{ option.label }}
            </span>
          </label>
        </div>
      </div>

      <!-- Smoking -->
      <div class="form-group">
        <label class="form-label">Курение</label>
        <div class="radio-group">
          <label class="radio-item" v-for="option in smokingOptions" :key="option.value">
            <input
              v-model="localData.smoking"
              type="radio"
              :value="option.value"
              name="smoking"
            />
            <span class="radio-label">
              <span class="radio-icon">{{ option.icon }}</span>
              {{ option.label }}
            </span>
          </label>
        </div>
      </div>

      <!-- Drinking -->
      <div class="form-group">
        <label class="form-label">Алкоголь</label>
        <div class="radio-group">
          <label class="radio-item" v-for="option in drinkingOptions" :key="option.value">
            <input
              v-model="localData.drinking"
              type="radio"
              :value="option.value"
              name="drinking"
            />
            <span class="radio-label">
              <span class="radio-icon">{{ option.icon }}</span>
              {{ option.label }}
            </span>
          </label>
        </div>
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

const languages = [
  { value: 'russian', label: 'Русский', icon: '🇷🇺' },
  { value: 'english', label: 'Английский', icon: '🇺🇸' },
  { value: 'german', label: 'Немецкий', icon: '🇩🇪' },
  { value: 'french', label: 'Французский', icon: '🇫🇷' },
  { value: 'spanish', label: 'Испанский', icon: '🇪🇸' },
  { value: 'italian', label: 'Итальянский', icon: '🇮🇹' },
  { value: 'chinese', label: 'Китайский', icon: '🇨🇳' },
  { value: 'japanese', label: 'Японский', icon: '🇯🇵' },
  { value: 'korean', label: 'Корейский', icon: '🇰🇷' },
  { value: 'arabic', label: 'Арабский', icon: '🇸🇦' }
]

const childrenOptions = [
  { value: true, label: 'Есть дети', icon: '👶' },
  { value: false, label: 'Нет детей', icon: '🚫' }
]

const wantsChildrenOptions = [
  { value: true, label: 'Хочу детей', icon: '👶' },
  { value: false, label: 'Не хочу детей', icon: '🚫' },
  { value: null, label: 'Не важно', icon: '❓' }
]

const smokingOptions = [
  { value: true, label: 'Курю', icon: '🚬' },
  { value: false, label: 'Не курю', icon: '🚫' },
  { value: null, label: 'Не важно', icon: '❓' }
]

const drinkingOptions = [
  { value: true, label: 'Пью', icon: '🍷' },
  { value: false, label: 'Не пью', icon: '🚫' },
  { value: null, label: 'Не важно', icon: '❓' }
]

watch(localData, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })
</script>

<style scoped>
.step-additional {
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

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-input {
  width: 100%;
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  background-color: var(--bg-primary);
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
}

.form-select {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 12px center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: 40px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.checkbox-item,
.radio-item {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"],
.radio-item input[type="radio"] {
  display: none;
}

.checkbox-label,
.radio-label {
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

.checkbox-item input[type="checkbox"]:checked + .checkbox-label,
.radio-item input[type="radio"]:checked + .radio-label {
  border-color: var(--primary-color);
  background-color: rgba(255, 107, 107, 0.05);
}

.checkbox-label:hover,
.radio-label:hover {
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.checkbox-icon,
.radio-icon {
  font-size: var(--font-size-md);
  margin-right: var(--spacing-sm);
}
</style>
