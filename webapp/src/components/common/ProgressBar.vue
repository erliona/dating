<template>
  <div class="progress-container" :class="{ 'progress-disabled': disabled }">
    <div class="progress-track" :style="trackStyle">
      <div 
        class="progress-fill" 
        :style="fillStyle"
        :class="{ 'progress-animated': animated }"
      ></div>
    </div>
    <div v-if="showLabel" class="progress-label">
      {{ labelText }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger'].includes(value)
  },
  showLabel: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: ''
  },
  animated: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const percentage = computed(() => {
  const clampedValue = Math.max(0, Math.min(props.value, props.max))
  return (clampedValue / props.max) * 100
})

const trackStyle = computed(() => {
  return {
    height: props.size === 'sm' ? '4px' : props.size === 'lg' ? '12px' : '8px'
  }
})

const fillStyle = computed(() => {
  return {
    width: `${percentage.value}%`,
    backgroundColor: getVariantColor(props.variant)
  }
})

const labelText = computed(() => {
  if (props.label) {
    return props.label
  }
  return `${Math.round(percentage.value)}%`
})

const getVariantColor = (variant) => {
  const colors = {
    primary: 'var(--primary-color)',
    success: 'var(--success-color)',
    warning: 'var(--warning-color)',
    danger: 'var(--danger-color)'
  }
  return colors[variant] || colors.primary
}
</script>

<style scoped>
.progress-container {
  width: 100%;
}

.progress-track {
  width: 100%;
  background-color: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-animated .progress-fill {
  animation: progress-shimmer 2s infinite;
}

@keyframes progress-shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.progress-animated .progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.4),
    transparent
  );
  background-size: 200px 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.progress-label {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
}

.progress-disabled .progress-fill {
  background-color: var(--text-secondary);
}

.progress-disabled .progress-label {
  color: var(--text-secondary);
}
</style>
