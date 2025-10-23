<template>
  <div class="empty-state">
    <div class="empty-content">
      <div class="empty-icon">
        <span class="icon">🔍</span>
      </div>
      
      <h3 class="empty-title">Пока что никого рядом</h3>
      
      <p class="empty-description">
        В вашем радиусе пока нет новых людей. 
        Попробуйте расширить поиск или зайдите позже!
      </p>

      <div class="empty-actions">
        <Button 
          variant="primary" 
          size="lg" 
          @click="expandSearch"
          fullWidth
        >
          Расширить поиск
        </Button>
        
        <Button 
          variant="outline" 
          size="lg" 
          @click="goToSettings"
          fullWidth
        >
          Настройки поиска
        </Button>
      </div>

      <div class="empty-tips">
        <h4>Советы для лучших результатов:</h4>
        <ul>
          <li>Расширьте радиус поиска</li>
          <li>Попробуйте разные возрастные диапазоны</li>
          <li>Обновите свои фотографии</li>
          <li>Заполните профиль на 100%</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import Button from '../common/Button.vue'

const router = useRouter()

const emit = defineEmits(['expand-search'])

const expandSearch = () => {
  emit('expand-search')
}

const goToSettings = () => {
  router.push('/settings')
}
</script>

<style scoped>
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--spacing-xl);
  background-color: var(--bg-primary);
}

.empty-content {
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.empty-icon {
  margin-bottom: var(--spacing-xl);
}

.empty-icon .icon {
  font-size: 4rem;
  display: block;
}

.empty-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.empty-description {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 var(--spacing-xl) 0;
}

.empty-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.empty-tips {
  background-color: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius);
  text-align: left;
}

.empty-tips h4 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.empty-tips ul {
  margin: 0;
  padding-left: var(--spacing-lg);
}

.empty-tips li {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.empty-tips li:last-child {
  margin-bottom: 0;
}
</style>
