<template>
  <div class="verification-badge" :class="badgeClass">
    <div class="badge-content">
      <span class="badge-icon">{{ badgeIcon }}</span>
      <span class="badge-text">{{ badgeText }}</span>
    </div>
    
    <div v-if="showDetails" class="verification-details">
      <p class="verification-message">{{ verificationMessage }}</p>
      
      <div v-if="status === 'pending'" class="verification-actions">
        <Button 
          variant="outline" 
          size="sm" 
          @click="checkStatus"
          :loading="checkingStatus"
        >
          Проверить статус
        </Button>
      </div>
      
      <div v-else-if="status === 'rejected'" class="verification-actions">
        <Button 
          variant="primary" 
          size="sm" 
          @click="requestVerification"
          :loading="requesting"
        >
          Подать заявку снова
        </Button>
        <p class="rejection-reason" v-if="rejectionReason">
          Причина: {{ rejectionReason }}
        </p>
      </div>
      
      <div v-else-if="status === 'none'" class="verification-actions">
        <Button 
          variant="primary" 
          size="sm" 
          @click="requestVerification"
          :loading="requesting"
        >
          Запросить верификацию
        </Button>
        <p class="verification-benefits">
          ✓ Верифицированные профили получают больше лайков<br>
          ✓ Синий значок доверия<br>
          ✓ Приоритет в поиске
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Button from '../common/Button.vue'

const props = defineProps({
  status: {
    type: String,
    default: 'none',
    validator: (value) => ['none', 'pending', 'approved', 'rejected'].includes(value)
  },
  rejectionReason: {
    type: String,
    default: ''
  },
  showDetails: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['request-verification', 'check-status'])

const requesting = ref(false)
const checkingStatus = ref(false)

const badgeClass = computed(() => {
  return `verification-${props.status}`
})

const badgeIcon = computed(() => {
  switch (props.status) {
    case 'approved':
      return '✅'
    case 'pending':
      return '⏳'
    case 'rejected':
      return '❌'
    default:
      return '🔒'
  }
})

const badgeText = computed(() => {
  switch (props.status) {
    case 'approved':
      return 'Верифицирован'
    case 'pending':
      return 'На рассмотрении'
    case 'rejected':
      return 'Отклонено'
    default:
      return 'Не верифицирован'
  }
})

const verificationMessage = computed(() => {
  switch (props.status) {
    case 'approved':
      return 'Ваш профиль успешно верифицирован! Пользователи видят синий значок доверия.'
    case 'pending':
      return 'Ваша заявка на верификацию рассматривается. Обычно это занимает 1-2 дня.'
    case 'rejected':
      return 'Ваша заявка на верификацию была отклонена. Вы можете подать заявку снова.'
    default:
      return 'Верификация подтверждает, что вы реальный человек. Это увеличивает доверие других пользователей.'
  }
})

const requestVerification = async () => {
  requesting.value = true
  try {
    emit('request-verification')
  } finally {
    requesting.value = false
  }
}

const checkStatus = async () => {
  checkingStatus.value = true
  try {
    emit('check-status')
  } finally {
    checkingStatus.value = false
  }
}
</script>

<style scoped>
.verification-badge {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.badge-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.verification-none .badge-content {
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.verification-pending .badge-content {
  background-color: rgba(var(--warning-rgb), 0.1);
  color: var(--warning-color);
  border: 1px solid var(--warning-color);
}

.verification-approved .badge-content {
  background-color: rgba(var(--success-rgb), 0.1);
  color: var(--success-color);
  border: 1px solid var(--success-color);
}

.verification-rejected .badge-content {
  background-color: rgba(var(--danger-rgb), 0.1);
  color: var(--danger-color);
  border: 1px solid var(--danger-color);
}

.badge-icon {
  font-size: var(--font-size-md);
}

.badge-text {
  font-weight: var(--font-weight-semibold);
}

.verification-details {
  background-color: var(--bg-secondary);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
}

.verification-message {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-md) 0;
  line-height: 1.4;
}

.verification-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rejection-reason {
  font-size: var(--font-size-xs);
  color: var(--danger-color);
  margin: var(--spacing-sm) 0 0 0;
  padding: var(--spacing-xs);
  background-color: rgba(var(--danger-rgb), 0.1);
  border-radius: var(--border-radius);
}

.verification-benefits {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin: var(--spacing-sm) 0 0 0;
  line-height: 1.4;
}
</style>
