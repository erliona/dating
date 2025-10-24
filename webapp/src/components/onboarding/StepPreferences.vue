<template>
  <div class="step-preferences">
    <div class="step-header">
      <h2>Ваши предпочтения</h2>
      <p>Настройте поиск подходящих людей</p>
    </div>

    <div class="step-content">
      <div class="form-group">
        <label class="form-label">Возрастной диапазон</label>
        <div class="age-range">
          <div class="range-item">
            <label class="range-label">От {{ preferences.min_age }} лет</label>
            <input 
              type="range" 
              v-model.number="preferences.min_age"
              min="18" 
              max="65"
              class="range-slider"
            />
          </div>
          <div class="range-item">
            <label class="range-label">До {{ preferences.max_age }} лет</label>
            <input 
              type="range" 
              v-model.number="preferences.max_age"
              min="18" 
              max="65"
              class="range-slider"
            />
          </div>
        </div>
        <p class="form-hint">Выберите возрастной диапазон для поиска</p>
      </div>

      <div class="form-group">
        <label class="form-label">Максимальное расстояние</label>
        <div class="distance-range">
          <label class="range-label">До {{ preferences.max_distance_km }} км</label>
          <input 
            type="range" 
            v-model.number="preferences.max_distance_km"
            min="1" 
            max="100"
            class="range-slider"
          />
        </div>
        <p class="form-hint">В каком радиусе искать людей</p>
      </div>

      <div class="form-group">
        <label class="form-label">Дополнительные фильтры</label>
        <div class="filters-grid">
          <label class="filter-option">
            <input 
              type="checkbox" 
              v-model="preferences.verified_only"
            />
            <span class="filter-label">Только верифицированные</span>
          </label>
          <label class="filter-option">
            <input 
              type="checkbox" 
              v-model="preferences.online_only"
            />
            <span class="filter-label">Только онлайн</span>
          </label>
          <label class="filter-option">
            <input 
              type="checkbox" 
              v-model="preferences.has_photos"
            />
            <span class="filter-label">С фотографиями</span>
          </label>
          <label class="filter-option">
            <input 
              type="checkbox" 
              v-model="preferences.has_bio"
            />
            <span class="filter-label">С описанием</span>
          </label>
        </div>
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
        fullWidth
      >
        Продолжить
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Button from '../common/Button.vue'

const emit = defineEmits(['next', 'back', 'update-data'])

const preferences = ref({
  min_age: 18,
  max_age: 35,
  max_distance_km: 25,
  verified_only: false,
  online_only: false,
  has_photos: true,
  has_bio: false
})

const handleNext = () => {
  emit('update-data', preferences.value)
  emit('next')
}

const handleBack = () => {
  emit('back')
}

// Watch for changes and emit updates
watch(preferences, (newPreferences) => {
  emit('update-data', newPreferences)
}, { deep: true })
</script>

<style scoped>
.step-preferences {
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.age-range {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.range-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.range-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.range-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--border-color);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
  border: none;
}

.range-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
  border: none;
}

.distance-range {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.filters-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.filter-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-option:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.filter-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary-color);
}

.filter-label {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.form-hint {
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