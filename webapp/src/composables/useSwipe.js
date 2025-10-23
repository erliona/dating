import { ref, onMounted, onUnmounted } from 'vue'

export function useSwipe() {
  const startX = ref(0)
  const startY = ref(0)
  const currentX = ref(0)
  const currentY = ref(0)
  const isDragging = ref(false)
  const threshold = 100 // Minimum distance for swipe action

  const onTouchStart = (event) => {
    const touch = event.touches[0]
    startX.value = touch.clientX
    startY.value = touch.clientY
    currentX.value = touch.clientX
    currentY.value = touch.clientY
    isDragging.value = true
  }

  const onTouchMove = (event) => {
    if (!isDragging.value) return

    const touch = event.touches[0]
    currentX.value = touch.clientX
    currentY.value = touch.clientY

    // Prevent default scrolling
    event.preventDefault()
  }

  const onTouchEnd = (event) => {
    if (!isDragging.value) return

    const deltaX = currentX.value - startX.value
    const deltaY = currentY.value - startY.value
    const absDeltaX = Math.abs(deltaX)
    const absDeltaY = Math.abs(deltaY)

    // Determine if it's a horizontal swipe
    if (absDeltaX > absDeltaY && absDeltaX > threshold) {
      if (deltaX > 0) {
        // Swipe right - Like
        return { action: 'like', delta: deltaX }
      } else {
        // Swipe left - Pass
        return { action: 'pass', delta: deltaX }
      }
    }

    isDragging.value = false
    return null
  }

  const getSwipeTransform = () => {
    if (!isDragging.value) return ''

    const deltaX = currentX.value - startX.value
    const deltaY = currentY.value - startY.value
    const rotation = deltaX * 0.1 // Rotation based on horizontal movement

    return `translateX(${deltaX}px) translateY(${deltaY}px) rotate(${rotation}deg)`
  }

  const getSwipeOpacity = () => {
    if (!isDragging.value) return 1

    const deltaX = Math.abs(currentX.value - startX.value)
    return Math.max(0.3, 1 - deltaX / 300)
  }

  const resetSwipe = () => {
    isDragging.value = false
    startX.value = 0
    startY.value = 0
    currentX.value = 0
    currentY.value = 0
  }

  return {
    isDragging,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    getSwipeTransform,
    getSwipeOpacity,
    resetSwipe
  }
}
