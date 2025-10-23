<template>
  <div 
    class="swipe-card"
    :style="cardStyle"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
  >
    <!-- Photo Carousel -->
    <div class="photo-container">
      <div 
        v-for="(photo, index) in candidate.photos" 
        :key="index"
        class="photo-slide"
        :class="{ active: currentPhotoIndex === index }"
      >
        <img :src="photo.url" :alt="`Photo ${index + 1}`" />
      </div>
      
      <!-- Photo Indicators -->
      <div v-if="candidate.photos.length > 1" class="photo-indicators">
        <span 
          v-for="(photo, index) in candidate.photos" 
          :key="index"
          class="indicator"
          :class="{ active: currentPhotoIndex === index }"
          @click="currentPhotoIndex = index"
        ></span>
      </div>
    </div>

    <!-- Card Content -->
    <div class="card-content">
      <!-- Name and Age -->
      <div class="name-age">
        <h3>{{ candidate.name }}, {{ candidate.age }}</h3>
        <div v-if="candidate.is_verified" class="verified-badge">
          ✅
        </div>
      </div>

      <!-- Distance -->
      <div v-if="candidate.distance" class="distance">
        📍 {{ candidate.distance }} км
      </div>

      <!-- Bio -->
      <div v-if="candidate.bio" class="bio">
        {{ candidate.bio }}
      </div>

      <!-- Interests -->
      <div v-if="candidate.interests && candidate.interests.length > 0" class="interests">
        <span 
          v-for="interest in candidate.interests.slice(0, 3)" 
          :key="interest"
          class="interest-tag"
        >
          {{ getInterestIcon(interest) }} {{ getInterestLabel(interest) }}
        </span>
      </div>
    </div>

    <!-- Swipe Overlay -->
    <div v-if="isDragging" class="swipe-overlay">
      <div v-if="swipeDirection === 'right'" class="swipe-indicator like">
        ❤️ LIKE
      </div>
      <div v-else-if="swipeDirection === 'left'" class="swipe-indicator pass">
        ✖️ PASS
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSwipe } from '../../composables/useSwipe'

const props = defineProps({
  candidate: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['swipe'])

const currentPhotoIndex = ref(0)
const { isDragging, onTouchStart, onTouchMove, onTouchEnd, getSwipeTransform, getSwipeOpacity } = useSwipe()

const swipeDirection = computed(() => {
  if (!isDragging.value) return null
  const transform = getSwipeTransform()
  if (transform.includes('translateX(')) {
    const x = parseFloat(transform.match(/translateX\(([^)]+)\)/)?.[1] || '0')
    return x > 0 ? 'right' : 'left'
  }
  return null
})

const cardStyle = computed(() => {
  return {
    transform: getSwipeTransform(),
    opacity: getSwipeOpacity()
  }
})

const getInterestIcon = (interest) => {
  const icons = {
    music: '🎵',
    movies: '🎬',
    books: '📚',
    travel: '✈️',
    sports: '⚽',
    fitness: '💪',
    cooking: '👨‍🍳',
    art: '🎨',
    photography: '📸',
    gaming: '🎮',
    dancing: '💃',
    nature: '🌿',
    animals: '🐕',
    technology: '💻',
    fashion: '👗',
    cars: '🚗',
    yoga: '🧘',
    reading: '📖',
    writing: '✍️',
    volunteering: '🤝',
    meditation: '🧘‍♀️',
    board_games: '🎲',
    hiking: '🥾',
    swimming: '🏊',
    cycling: '🚴',
    running: '🏃',
    painting: '🖌️',
    gardening: '🌱',
    wine: '🍷'
  }
  return icons[interest] || '⭐'
}

const getInterestLabel = (interest) => {
  const labels = {
    music: 'Музыка',
    movies: 'Кино',
    books: 'Книги',
    travel: 'Путешествия',
    sports: 'Спорт',
    fitness: 'Фитнес',
    cooking: 'Кулинария',
    art: 'Искусство',
    photography: 'Фотография',
    gaming: 'Игры',
    dancing: 'Танцы',
    nature: 'Природа',
    animals: 'Животные',
    technology: 'Технологии',
    fashion: 'Мода',
    cars: 'Автомобили',
    yoga: 'Йога',
    reading: 'Чтение',
    writing: 'Письмо',
    volunteering: 'Волонтерство',
    meditation: 'Медитация',
    board_games: 'Настольные игры',
    hiking: 'Походы',
    swimming: 'Плавание',
    cycling: 'Велоспорт',
    running: 'Бег',
    painting: 'Живопись',
    gardening: 'Садоводство',
    wine: 'Вино'
  }
  return labels[interest] || interest
}

// Handle swipe end
const handleSwipeEnd = (result) => {
  if (result) {
    emit('swipe', result.action)
  }
}

// Override onTouchEnd to handle swipe result
const originalOnTouchEnd = onTouchEnd
onTouchEnd = (event) => {
  const result = originalOnTouchEnd(event)
  handleSwipeEnd(result)
}
</script>

<style scoped>
.swipe-card {
  width: 100%;
  height: 100%;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-large);
  overflow: hidden;
  position: relative;
  cursor: grab;
  user-select: none;
}

.swipe-card:active {
  cursor: grabbing;
}

.photo-container {
  position: relative;
  height: 70%;
  overflow: hidden;
}

.photo-slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.photo-slide.active {
  opacity: 1;
}

.photo-slide img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-indicators {
  position: absolute;
  bottom: var(--spacing-md);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: var(--spacing-xs);
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.indicator.active {
  background-color: white;
}

.card-content {
  padding: var(--spacing-lg);
  height: 30%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.name-age {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.name-age h3 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  color: var(--text-primary);
}

.verified-badge {
  font-size: var(--font-size-lg);
}

.distance {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.bio {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: var(--spacing-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.interests {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.interest-tag {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-small);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.swipe-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.swipe-indicator {
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-bold);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.swipe-indicator.like {
  background-color: rgba(255, 107, 107, 0.9);
  color: white;
  transform: rotate(15deg);
}

.swipe-indicator.pass {
  background-color: rgba(108, 117, 125, 0.9);
  color: white;
  transform: rotate(-15deg);
}
</style>
