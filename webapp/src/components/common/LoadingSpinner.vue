<template>
  <div class="spinner-container" :class="{ 'spinner-overlay': overlay }">
    <div class="spinner" :class="spinnerClasses">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <div v-if="text" class="spinner-text">{{ text }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value)
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'white'].includes(value)
  },
  text: {
    type: String,
    default: ''
  },
  overlay: {
    type: Boolean,
    default: false
  }
})

const spinnerClasses = computed(() => {
  return [
    `spinner-${props.size}`,
    `spinner-${props.variant}`
  ]
})
</script>

<style scoped>
.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.spinner-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 1000;
}

.spinner {
  position: relative;
  display: inline-block;
}

.spinner-ring {
  position: absolute;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Sizes */
.spinner-sm {
  width: 16px;
  height: 16px;
}

.spinner-sm .spinner-ring {
  width: 16px;
  height: 16px;
  border-width: 1px;
}

.spinner-md {
  width: 16px;
  height: 16px;
}

.spinner-md .spinner-ring {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.spinner-lg {
  width: 32px;
  height: 32px;
}

.spinner-lg .spinner-ring {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

.spinner-xl {
  width: 48px;
  height: 48px;
}

.spinner-xl .spinner-ring {
  width: 48px;
  height: 48px;
  border-width: 4px;
}

/* Variants */
.spinner-primary {
  color: var(--primary-color);
}

.spinner-secondary {
  color: var(--text-secondary);
}

.spinner-white {
  color: white;
}

.spinner-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
}

.spinner-overlay .spinner-text {
  color: var(--text-primary);
}
</style>
