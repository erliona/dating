<template>
  <div class="step-bio">
    <div class="step-header">
      <h2>Расскажите о себе</h2>
      <p>Напишите короткое описание (необязательно)</p>
    </div>

    <div class="step-content">
      <div class="form-group">
        <label class="form-label">О себе</label>
        <textarea
          v-model="localData.bio"
          class="form-input form-textarea"
          placeholder="Расскажите что-то интересное о себе..."
          maxlength="500"
          rows="6"
        ></textarea>
        <div class="char-counter">
          {{ localData.bio.length }}/500
        </div>
      </div>

      <div class="bio-tips">
        <h4>Советы для хорошего описания:</h4>
        <ul>
          <li>Расскажите о своих интересах и хобби</li>
          <li>Упомяните что ищете в отношениях</li>
          <li>Будьте позитивными и искренними</li>
          <li>Избегайте клише и общих фраз</li>
        </ul>
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

watch(localData, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true })
</script>

<style scoped>
.step-bio {
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
  margin-bottom: var(--spacing-xl);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

.char-counter {
  text-align: right;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.bio-tips {
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius);
}

.bio-tips h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.bio-tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.bio-tips li {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
  padding-left: var(--spacing-md);
  position: relative;
}

.bio-tips li::before {
  content: '💡';
  position: absolute;
  left: 0;
}
</style>
