<template>
  <button 
    :class="buttonClasses"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot></slot>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'outline', 'danger', 'icon'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  fullWidth: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  return [
    'btn',
    `btn-${props.variant}`,
    `btn-${props.size}`,
    {
      'btn-disabled': props.disabled,
      'btn-full-width': props.fullWidth
    }
  ]
})
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  border: none;
  border-radius: var(--border-radius);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

/* Variants */
.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(.btn-disabled) {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-medium);
}

.btn-secondary {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(.btn-disabled) {
  background-color: var(--bg-primary);
  border-color: var(--primary-color);
}

.btn-outline {
  background-color: transparent;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}

.btn-outline:hover:not(.btn-disabled) {
  background-color: var(--primary-color);
  color: white;
}

.btn-danger {
  background-color: var(--danger-color);
  color: white;
}

.btn-danger:hover:not(.btn-disabled) {
  background-color: var(--danger-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-medium);
}

.btn-icon {
  background-color: transparent;
  color: var(--text-primary);
  border: none;
  padding: var(--spacing-sm);
  border-radius: 50%;
}

.btn-icon:hover:not(.btn-disabled) {
  background-color: var(--bg-secondary);
}

/* Sizes */
.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
  min-height: 32px;
}

.btn-md {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-md);
  min-height: 40px;
}

.btn-lg {
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-size-lg);
  min-height: 48px;
}

/* States */
.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.btn-full-width {
  width: 100%;
}

/* Focus */
.btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.3);
}

.btn-outline:focus {
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.3);
}

.btn-icon:focus {
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.3);
}
</style>
