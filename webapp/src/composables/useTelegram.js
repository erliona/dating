import { ref, onMounted } from 'vue'

export function useTelegram() {
  const tg = ref(null)
  const user = ref(null)
  const isReady = ref(false)

  const initTelegram = () => {
    if (window.Telegram?.WebApp) {
      tg.value = window.Telegram.WebApp
      user.value = tg.value.initDataUnsafe?.user
      isReady.value = true
      
      // Configure Telegram WebApp
      tg.value.ready()
      tg.value.expand()
      
      // Set theme
      document.body.style.backgroundColor = tg.value.themeParams.bg_color || '#ffffff'
      document.body.style.color = tg.value.themeParams.text_color || '#000000'
      
      console.log('Telegram WebApp initialized:', {
        user: user.value,
        theme: tg.value.themeParams
      })
    } else {
      console.warn('Telegram WebApp not available')
    }
  }

  const getTelegramData = () => {
    if (!tg.value) return null
    
    return {
      user: user.value,
      initData: tg.value.initData,
      initDataUnsafe: tg.value.initDataUnsafe,
      version: tg.value.version,
      platform: tg.value.platform,
      colorScheme: tg.value.colorScheme,
      themeParams: tg.value.themeParams
    }
  }

  const showAlert = (message) => {
    if (tg.value) {
      tg.value.showAlert(message)
    } else {
      alert(message)
    }
  }

  const showConfirm = (message) => {
    if (tg.value) {
      return new Promise((resolve) => {
        tg.value.showConfirm(message, resolve)
      })
    } else {
      return Promise.resolve(confirm(message))
    }
  }

  const showPopup = (params) => {
    if (tg.value) {
      return new Promise((resolve) => {
        tg.value.showPopup(params, resolve)
      })
    } else {
      return Promise.resolve(true)
    }
  }

  const close = () => {
    if (tg.value) {
      tg.value.close()
    }
  }

  const hapticFeedback = (type = 'impact') => {
    if (tg.value?.HapticFeedback) {
      switch (type) {
        case 'impact':
          tg.value.HapticFeedback.impactOccurred('medium')
          break
        case 'notification':
          tg.value.HapticFeedback.notificationOccurred('success')
          break
        case 'selection':
          tg.value.HapticFeedback.selectionChanged()
          break
      }
    }
  }

  const setHeaderColor = (color) => {
    if (tg.value) {
      tg.value.setHeaderColor(color)
    }
  }

  const setBackgroundColor = (color) => {
    if (tg.value) {
      tg.value.setBackgroundColor(color)
    }
  }

  onMounted(() => {
    initTelegram()
  })

  return {
    tg,
    user,
    isReady,
    initTelegram,
    getTelegramData,
    showAlert,
    showConfirm,
    showPopup,
    close,
    hapticFeedback,
    setHeaderColor,
    setBackgroundColor
  }
}
