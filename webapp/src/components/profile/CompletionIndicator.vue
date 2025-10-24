<template>
  <div class="completion-indicator">
    <div class="completion-header">
      <h4>Завершенность профиля</h4>
      <span class="completion-percentage">{{ percentage }}%</span>
    </div>
    
    <div class="completion-bar">
      <div 
        class="completion-fill" 
        :style="{ width: percentage + '%' }"
        :class="getCompletionClass(percentage)"
      ></div>
    </div>
    
    <div v-if="percentage < 100" class="completion-tips">
      <p class="completion-message">{{ getCompletionMessage() }}</p>
      <div class="missing-fields">
        <h5>Добавьте для лучших совпадений:</h5>
        <ul>
          <li v-for="tip in completionTips" :key="tip.field" class="completion-tip">
            <span class="tip-icon">{{ tip.icon }}</span>
            <span class="tip-text">{{ tip.text }}</span>
            <span class="tip-impact">+{{ tip.impact }}%</span>
          </li>
        </ul>
      </div>
    </div>
    
    <div v-else class="completion-complete">
      <div class="complete-icon">🎉</div>
      <p>Отлично! Ваш профиль заполнен на 100%</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: {
    type: Object,
    required: true
  }
})

const percentage = computed(() => {
  if (!props.profile) return 0
  
  const fields = [
    'name', 'birth_date', 'gender', 'orientation', 'goal', 'bio',
    'interests', 'height_cm', 'education', 'profession', 'languages'
  ]
  
  const completedFields = fields.filter(field => {
    const value = props.profile[field]
    return value !== null && value !== undefined && value !== '' && 
           (Array.isArray(value) ? value.length > 0 : true)
  }).length
  
  const photoCount = props.profile.photos?.length || 0
  const photoScore = Math.min(photoCount, 3) / 3
  
  return Math.round(((completedFields + photoScore) / (fields.length + 1)) * 100)
})

const completionTips = computed(() => {
  const tips = []
  
  if (!props.profile.bio || props.profile.bio.trim().length === 0) {
    tips.push({
      field: 'bio',
      icon: '💬',
      text: 'Добавьте описание о себе',
      impact: 15
    })
  }
  
  if (!props.profile.interests || props.profile.interests.length === 0) {
    tips.push({
      field: 'interests',
      icon: '⭐',
      text: 'Выберите интересы',
      impact: 15
    })
  }
  
  if (!props.profile.photos || props.profile.photos.length < 3) {
    tips.push({
      field: 'photos',
      icon: '📸',
      text: `Добавьте ${3 - (props.profile.photos?.length || 0)} фото`,
      impact: 20
    })
  }
  
  if (!props.profile.height_cm) {
    tips.push({
      field: 'height',
      icon: '📏',
      text: 'Укажите рост',
      impact: 5
    })
  }
  
  if (!props.profile.education) {
    tips.push({
      field: 'education',
      icon: '🎓',
      text: 'Укажите образование',
      impact: 5
    })
  }
  
  if (!props.profile.profession) {
    tips.push({
      field: 'profession',
      icon: '💼',
      text: 'Укажите профессию',
      impact: 5
    })
  }
  
  return tips.slice(0, 4) // Show max 4 tips
})

const getCompletionClass = (percentage) => {
  if (percentage >= 100) return 'complete'
  if (percentage >= 80) return 'good'
  if (percentage >= 60) return 'okay'
  return 'poor'
}

const getCompletionMessage = () => {
  if (percentage.value >= 80) {
    return 'Отличный профиль! Добавьте еще несколько деталей для идеального результата.'
  } else if (percentage.value >= 60) {
    return 'Хорошее начало! Заполните профиль для лучших совпадений.'
  } else {
    return 'Профиль почти готов! Добавьте больше информации о себе.'
  }
}
</script>

<style scoped>
.completion-indicator {
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-lg);
}

.completion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.completion-header h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0;
  color: var(--text-primary);
}

.completion-percentage {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--primary-color);
}

.completion-bar {
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-md);
}

.completion-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.completion-fill.poor {
  background-color: var(--danger-color);
}

.completion-fill.okay {
  background-color: var(--warning-color);
}

.completion-fill.good {
  background-color: var(--primary-color);
}

.completion-fill.complete {
  background-color: var(--success-color);
}

.completion-message {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.missing-fields h5 {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.missing-fields ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.completion-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-color);
}

.completion-tip:last-child {
  border-bottom: none;
}

.tip-icon {
  font-size: var(--font-size-md);
  flex-shrink: 0;
}

.tip-text {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.tip-impact {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  color: var(--primary-color);
  background-color: rgba(var(--primary-rgb), 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.completion-complete {
  text-align: center;
  padding: var(--spacing-lg);
}

.complete-icon {
  font-size: 2rem;
  margin-bottom: var(--spacing-sm);
}

.completion-complete p {
  font-size: var(--font-size-md);
  color: var(--success-color);
  font-weight: var(--font-weight-medium);
  margin: 0;
}
</style>
