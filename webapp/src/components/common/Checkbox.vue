<template>
  <label class="checkbox-wrapper" :class="{ 'checkbox-disabled': disabled }">
    <input
      :id="checkboxId"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="checkbox-input"
      @change="handleChange"
    />
    <span class="checkbox-custom"></span>
    <span v-if="label" class="checkbox-label">{{ label }}</span>
  </label>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const checkboxId = ref(`checkbox-${Math.random().toString(36).substr(2, 9)}`)

const handleChange = (event) => {
  const checked = event.target.checked
  emit('update:modelValue', checked)
  emit('change', checked)
}
</script>

<style scoped>
.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  user-select: none;
}

.checkbox-wrapper:hover:not(.checkbox-disabled) .checkbox-custom {
  border-color: var(--primary-color);
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkbox-custom {
  position: relative;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  background-color: white;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.checkbox-custom::after {
  content: "";
  position: absolute;
  display: none;
  left: 6px;
  top: 2px;
  width: 6px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-input:checked ~ .checkbox-custom {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.checkbox-input:checked ~ .checkbox-custom::after {
  display: block;
}

.checkbox-input:focus ~ .checkbox-custom {
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}

.checkbox-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  line-height: 1.4;
}

.checkbox-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-disabled .checkbox-custom {
  background-color: var(--bg-secondary);
  border-color: var(--border-color);
}

.checkbox-disabled .checkbox-label {
  color: var(--text-secondary);
}
</style>
