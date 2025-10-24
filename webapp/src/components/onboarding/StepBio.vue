<template>
  <div class="step-bio">
    <div class="step-header">
      <h2>Расскажите о себе</h2>
      <p>Поделитесь чем-то интересным</p>
    </div>

    <div class="step-content">
      <div class="form-group">
        <label class="form-label">Био (необязательно)</label>
        <textarea 
          v-model="formData.bio" 
          placeholder="Расскажите о себе, своих интересах, что ищете..."
          maxlength="500"
          rows="6"
          class="bio-textarea"
        ></textarea>
        <div class="char-count">
          {{ formData.bio?.length || 0 }}/500
        </div>
      </div>

      <div class="bio-tips">
        <h4>Советы для хорошего био:</h4>
        <ul>
          <li>Расскажите о своих увлечениях</li>
          <li>Упомяните что ищете в отношениях</li>
          <li>Добавьте что-то уникальное о себе</li>
          <li>Избегайте клише и общих фраз</li>
        </ul>
      </div>

      <div class="bio-examples">
        <h4>Примеры хороших био:</h4>
        <div class="example-bio" @click="useExample(0)">
          "Люблю путешествовать и открывать новые места. Ищу человека, с которым можно будет исследовать мир вместе 🌍"
        </div>
        <div class="example-bio" @click="useExample(1)">
          "Фотограф по профессии, кофеман по призванию. Ищу того, кто разделит со мной утренний кофе и вечерние прогулки ☕"
        </div>
        <div class="example-bio" @click="useExample(2)">
          "Увлекаюсь йогой и здоровым образом жизни. Ищу партнера для совместных тренировок и активного отдыха 🧘‍♀️"
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

const bioExamples = [
  "Люблю путешествовать и открывать новые места. Ищу человека, с которым можно будет исследовать мир вместе 🌍",
  "Фотограф по профессии, кофеман по призванию. Ищу того, кто разделит со мной утренний кофе и вечерние прогулки ☕",
  "Увлекаюсь йогой и здоровым образом жизни. Ищу партнера для совместных тренировок и активного отдыха 🧘‍♀️"
]

const useExample = (index) => {
  formData.value.bio = bioExamples[index]
}

const handleNext = () => {
  emit('next')
}

const handleBack = () => {
  emit('back')
}
</script>

<style scoped>
.step-bio {
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
  gap: var(--spacing-sm);
}

.form-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.bio-textarea {
  width: 100%;
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  font-family: inherit;
  line-height: 1.5;
  resize: vertical;
  min-height: 120px;
  transition: border-color 0.2s ease;
}

.bio-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.char-count {
  text-align: right;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.bio-tips {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
}

.bio-tips h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.bio-tips ul {
  margin: 0;
  padding-left: var(--spacing-md);
}

.bio-tips li {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.bio-tips li:last-child {
  margin-bottom: 0;
}

.bio-examples {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
}

.bio-examples h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.example-bio {
  background-color: white;
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: var(--spacing-sm);
}

.example-bio:hover {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.05);
}

.example-bio:last-child {
  margin-bottom: 0;
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