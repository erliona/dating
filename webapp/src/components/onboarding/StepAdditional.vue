<template>
  <div class="step-additional">
    <div class="step-header">
      <h2>Дополнительная информация</h2>
      <p>Расскажите больше о себе (все поля необязательные)</p>
    </div>

    <div class="step-content">
      <div class="form-section">
        <h3>Основное</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Рост (см)</label>
            <input 
              v-model.number="formData.height_cm" 
              type="number" 
              placeholder="170"
              min="120"
              max="220"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Образование</label>
            <select v-model="formData.education" class="form-select">
              <option value="">Выберите</option>
              <option value="school">Среднее</option>
              <option value="college">Среднее специальное</option>
              <option value="university">Высшее</option>
              <option value="postgraduate">Аспирантура</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Профессия</label>
          <input 
            v-model="formData.profession" 
            type="text" 
            placeholder="Ваша профессия"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label">Языки</label>
          <input 
            v-model="formData.languages" 
            type="text" 
            placeholder="Русский, English, Deutsch"
            class="form-input"
          />
        </div>
      </div>

      <div class="form-section">
        <h3>Семья и дети</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Дети</label>
            <select v-model="formData.has_children" class="form-select">
              <option value="">Не указано</option>
              <option :value="true">Есть</option>
              <option :value="false">Нет</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Хочу детей</label>
            <select v-model="formData.wants_children" class="form-select">
              <option value="">Не указано</option>
              <option :value="true">Да</option>
              <option :value="false">Нет</option>
            </select>
          </div>
        </div>
      </div>

      <div class="form-section">
        <h3>Привычки</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Курение</label>
            <select v-model="formData.smoking" class="form-select">
              <option value="">Не указано</option>
              <option value="never">Никогда</option>
              <option value="occasionally">Иногда</option>
              <option value="regularly">Регулярно</option>
              <option value="quit">Бросил(а)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Алкоголь</label>
            <select v-model="formData.drinking" class="form-select">
              <option value="">Не указано</option>
              <option value="never">Никогда</option>
              <option value="occasionally">Иногда</option>
              <option value="regularly">Регулярно</option>
              <option value="quit">Бросил(а)</option>
            </select>
          </div>
        </div>
      </div>

      <div class="optional-note">
        <p>💡 Все поля необязательные - заполняйте только то, что хотите рассказать о себе</p>
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

const formData = ref({
  height_cm: null,
  education: '',
  profession: '',
  languages: '',
  has_children: null,
  wants_children: null,
  smoking: '',
  drinking: ''
})

const handleNext = () => {
  emit('update-data', formData.value)
  emit('next')
}

const handleBack = () => {
  emit('back')
}

// Watch for changes and emit updates
watch(formData, (newData) => {
  emit('update-data', newData)
}, { deep: true })
</script>

<style scoped>
.step-additional {
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
  overflow-y: auto;
}

.form-section {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
}

.form-section h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  background-color: white;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-input::placeholder {
  color: var(--text-secondary);
}

.optional-note {
  text-align: center;
  padding: var(--spacing-md);
  background-color: rgba(var(--primary-rgb), 0.1);
  border-radius: var(--border-radius);
  border: 1px solid rgba(var(--primary-rgb), 0.2);
}

.optional-note p {
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

@media (max-width: 480px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>