<template>
  <div class="input-group">
    <label v-if="label" class="input-label" :for="inputId">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    <div class="input-wrapper" :class="{ 'input-error': hasError, 'input-disabled': disabled }">
      <input
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :maxlength="maxlength"
        :min="min"
        :max="max"
        :step="step"
        :autocomplete="autocomplete"
        class="input-field"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      <div v-if="hasError" class="input-error-icon">
        ⚠️
      </div>
    </div>
    <div v-if="hasError" class="input-error-message">
      {{ errorMessage }}
    </div>
    <div v-if="hint && !hasError" class="input-hint">
      {{ hint }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  maxlength: {
    type: Number,
    default: null
  },
  min: {
    type: Number,
    default: null
  },
  max: {
    type: Number,
    default: null
  },
  step: {
    type: Number,
    default: null
  },
  autocomplete: {
    type: String,
    default: 'off'
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus'])

const inputId = ref(`input-${Math.random().toString(36).substr(2, 9)}`)
const isFocused = ref(false)

const hasError = computed(() => {
  return props.error && props.error.length > 0
})

const errorMessage = computed(() => {
  return props.error
})

const handleInput = (event) => {
  let value = event.target.value
  
  // Handle number inputs
  if (props.type === 'number') {
    value = value === '' ? null : Number(value)
  }
  
  emit('update:modelValue', value)
}

const handleBlur = (event) => {
  isFocused.value = false
  emit('blur', event)
}

const handleFocus = (event) => {
  isFocused.value = true
  emit('focus', event)
}
</script>

<style scoped>
.input-group {
  margin-bottom: var(--spacing-md);
}

.input-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

.required {
  color: var(--danger-color);
  margin-left: 2px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-field {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: var(--font-size-md);
  background-color: white;
  transition: all 0.2s ease;
}

.input-field:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}

.input-field::placeholder {
  color: var(--text-secondary);
}

.input-field:disabled {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.input-error .input-field {
  border-color: var(--danger-color);
}

.input-error .input-field:focus {
  border-color: var(--danger-color);
  box-shadow: 0 0 0 3px rgba(var(--danger-rgb), 0.1);
}

.input-disabled .input-field {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.input-error-icon {
  position: absolute;
  right: var(--spacing-sm);
  color: var(--danger-color);
  font-size: var(--font-size-sm);
}

.input-error-message {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--danger-color);
}

.input-hint {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

/* Number input specific styles */
.input-field[type="number"] {
  -moz-appearance: textfield;
}

.input-field[type="number"]::-webkit-outer-spin-button,
.input-field[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Range input specific styles */
.input-field[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  outline: none;
  padding: 0;
}

.input-field[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
  border: none;
}

.input-field[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
  border: none;
}

/* Textarea specific styles */
.input-field[type="textarea"] {
  resize: vertical;
  min-height: 80px;
}
</style>
