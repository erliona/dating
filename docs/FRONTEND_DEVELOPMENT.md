# Frontend Development Standards

## Overview

This document defines the frontend development standards for the dating application, covering Vue 3, Vite, Pinia, and Telegram WebApp integration.

## Technology Stack

### Core Technologies
- **Vue 3.4+**: Reactive framework with Composition API
- **Vite 5.0+**: Fast build tool and development server
- **Pinia 2.1+**: State management library
- **Vue Router 4.2+**: Client-side routing
- **Axios 1.6+**: HTTP client for API communication

### Development Tools
- **@vitejs/plugin-vue**: Vue SFC support for Vite
- **Terser**: JavaScript minification
- **ESLint**: Code linting (recommended)
- **Prettier**: Code formatting (recommended)

## Project Structure

```
webapp/
├── src/
│   ├── components/          # Reusable Vue components
│   │   ├── common/          # Generic UI components
│   │   ├── chat/           # Chat-specific components
│   │   ├── discovery/      # Discovery/swipe components
│   │   ├── onboarding/     # Onboarding flow components
│   │   └── profile/        # Profile management components
│   ├── composables/        # Reusable composition functions
│   ├── stores/            # Pinia stores
│   ├── router/            # Vue Router configuration
│   ├── views/             # Page components
│   ├── utils/             # Utility functions
│   └── assets/            # Static assets
├── public/                # Public static files
├── index.html             # Entry HTML file
├── vite.config.js         # Vite configuration
└── package.json           # Dependencies and scripts
```

## Vue 3 Development Standards

### Component Structure

Use Single File Components (SFC) with Composition API:

```vue
<template>
  <div class="component-name">
    <h1>{{ title }}</h1>
    <button @click="handleClick">Click me</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

// Props definition
const props = defineProps<{
  title: string
  isActive?: boolean
}>()

// Emits definition
const emit = defineEmits<{
  click: [payload: { id: string }]
}>()

// Reactive state
const count = ref(0)
const userStore = useUserStore()

// Computed properties
const doubleCount = computed(() => count.value * 2)

// Methods
const handleClick = () => {
  count.value++
  emit('click', { id: 'button' })
}

// Lifecycle
onMounted(() => {
  console.log('Component mounted')
})
</script>

<style scoped>
.component-name {
  padding: 1rem;
}
</style>
```

### Composition API Best Practices

#### Reactive State
```javascript
// ✅ GOOD: Use ref for primitives
const count = ref(0)
const message = ref('Hello')

// ✅ GOOD: Use reactive for objects
const user = reactive({
  name: '',
  email: ''
})

// ✅ GOOD: Use computed for derived state
const fullName = computed(() => `${user.firstName} ${user.lastName}`)
```

#### Lifecycle Hooks
```javascript
import { onMounted, onUnmounted, onUpdated } from 'vue'

onMounted(() => {
  // Component mounted
})

onUnmounted(() => {
  // Cleanup
})

onUpdated(() => {
  // Component updated
})
```

#### Watchers
```javascript
import { watch, watchEffect } from 'vue'

// Watch specific reactive value
watch(count, (newValue, oldValue) => {
  console.log(`Count changed from ${oldValue} to ${newValue}`)
})

// Watch multiple values
watch([count, message], ([newCount, newMessage]) => {
  console.log('Count or message changed')
})

// Watch effect (automatic dependency tracking)
watchEffect(() => {
  console.log(`Count is ${count.value}`)
})
```

## Pinia State Management

### Store Structure

```javascript
// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '@/composables/useApi'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || 'Guest')

  // Actions
  const fetchUser = async () => {
    try {
      isLoading.value = true
      error.value = null
      const response = await useApi().get('/user/profile')
      user.value = response.data
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  const updateUser = async (userData) => {
    try {
      isLoading.value = true
      const response = await useApi().put('/user/profile', userData)
      user.value = response.data
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    user.value = null
    // Clear other stores if needed
  }

  return {
    // State
    user,
    isLoading,
    error,
    // Getters
    isAuthenticated,
    userName,
    // Actions
    fetchUser,
    updateUser,
    logout
  }
})
```

### Store Usage in Components

```vue
<script setup>
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const userStore = useUserStore()

// Destructure reactive state
const { user, isLoading, error } = storeToRefs(userStore)

// Use actions
const handleUpdate = () => {
  userStore.updateUser({ name: 'New Name' })
}
</script>
```

## Composables

### Reusable Logic

```javascript
// composables/useApi.js
import axios from 'axios'
import { ref } from 'vue'

export function useApi() {
  const isLoading = ref(false)
  const error = ref(null)

  const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000
  })

  // Request interceptor
  api.interceptors.request.use((config) => {
    isLoading.value = true
    error.value = null
    
    // Add JWT token if available
    const token = localStorage.getItem('jwt_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  })

  // Response interceptor
  api.interceptors.response.use(
    (response) => {
      isLoading.value = false
      return response
    },
    (err) => {
      isLoading.value = false
      error.value = err.response?.data?.message || err.message
      return Promise.reject(err)
    }
  )

  return {
    api,
    isLoading,
    error
  }
}
```

### Telegram WebApp Integration

```javascript
// composables/useTelegram.js
import { ref, computed } from 'vue'

export function useTelegram() {
  const webApp = ref(null)
  const user = ref(null)
  const theme = ref('light')

  const initTelegram = () => {
    if (window.Telegram?.WebApp) {
      webApp.value = window.Telegram.WebApp
      user.value = webApp.value.initDataUnsafe?.user
      theme.value = webApp.value.colorScheme || 'light'
      
      // Enable closing confirmation
      webApp.value.enableClosingConfirmation()
      
      // Expand the app
      webApp.value.expand()
    }
  }

  const sendData = (data) => {
    if (webApp.value) {
      webApp.value.sendData(JSON.stringify(data))
    }
  }

  const showAlert = (message) => {
    if (webApp.value) {
      webApp.value.showAlert(message)
    }
  }

  const showConfirm = (message) => {
    if (webApp.value) {
      return webApp.value.showConfirm(message)
    }
    return Promise.resolve(false)
  }

  const isDark = computed(() => theme.value === 'dark')
  const isLight = computed(() => theme.value === 'light')

  return {
    webApp,
    user,
    theme,
    isDark,
    isLight,
    initTelegram,
    sendData,
    showAlert,
    showConfirm
  }
}
```

## Vue Router Configuration

### Route Structure

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('@/views/WelcomeView.vue')
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/OnboardingView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/discovery',
    name: 'Discovery',
    component: () => import('@/views/DiscoveryView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
```

### Admin Routes

```javascript
// router/admin.js
import { createRouter, createWebHistory } from 'vue-router'

const adminRoutes = [
  {
    path: '/admin',
    name: 'AdminLogin',
    component: () => import('@/views/AdminLogin.vue')
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue'),
    meta: { requiresAdminAuth: true }
  }
]

export const adminRouter = createRouter({
  history: createWebHistory(),
  routes: adminRoutes
})
```

## Component Development

### Component Naming

```vue
<!-- ✅ GOOD: PascalCase for components -->
<template>
  <SwipeCard :profile="profile" @swipe="handleSwipe" />
</template>

<!-- ❌ BAD: kebab-case -->
<template>
  <swipe-card :profile="profile" @swipe="handleSwipe" />
</template>
```

### Props and Emits

```vue
<script setup>
// ✅ GOOD: TypeScript-like props
const props = defineProps<{
  profile: {
    id: string
    name: string
    age: number
    photos: string[]
  }
  isActive?: boolean
}>()

// ✅ GOOD: TypeScript-like emits
const emit = defineEmits<{
  swipe: [direction: 'left' | 'right']
  like: [profileId: string]
}>()

// ✅ GOOD: Default values
const { isActive = false } = props
</script>
```

### Event Handling

```vue
<template>
  <div @click="handleClick" @keydown.enter="handleClick">
    <button @click.stop="handleButtonClick">Button</button>
  </div>
</template>

<script setup>
const handleClick = (event) => {
  console.log('Clicked', event)
}

const handleButtonClick = (event) => {
  event.stopPropagation()
  console.log('Button clicked')
}
</script>
```

## Styling Standards

### CSS Scoping

```vue
<style scoped>
/* ✅ GOOD: Scoped styles */
.component-name {
  padding: 1rem;
}

.component-name .button {
  background: var(--tg-theme-button-color);
}
</style>

<style>
/* ✅ GOOD: Global styles when needed */
:root {
  --tg-theme-bg-color: #ffffff;
  --tg-theme-text-color: #000000;
}
</style>
```

### Telegram Theme Integration

```css
/* Use Telegram theme variables */
body {
  background-color: var(--tg-theme-bg-color);
  color: var(--tg-theme-text-color);
}

.button {
  background-color: var(--tg-theme-button-color);
  color: var(--tg-theme-button-text-color);
}

.hint {
  color: var(--tg-theme-hint-color);
}

.link {
  color: var(--tg-theme-link-color);
}
```

## Performance Optimization

### Lazy Loading

```javascript
// ✅ GOOD: Lazy load components
const LazyComponent = defineAsyncComponent(() => import('./HeavyComponent.vue'))

// ✅ GOOD: Lazy load routes
const routes = [
  {
    path: '/admin',
    component: () => import('@/views/AdminView.vue')
  }
]
```

### Code Splitting

```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          telegram: ['axios']
        }
      }
    }
  }
})
```

## Error Handling

### Global Error Handling

```javascript
// main.js
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // Send error to monitoring service
  // sendErrorToMonitoring(err)
}

app.mount('#app')
```

### Component Error Boundaries

```vue
<template>
  <div v-if="hasError" class="error-boundary">
    <h2>Something went wrong</h2>
    <button @click="retry">Try again</button>
  </div>
  <div v-else>
    <slot />
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)

onErrorCaptured((err, instance, info) => {
  hasError.value = true
  console.error('Component error:', err)
  return false // Prevent error from propagating
})

const retry = () => {
  hasError.value = false
}
</script>
```

## Testing Standards

### Component Testing

```javascript
// Component.test.js
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import SwipeCard from '@/components/discovery/SwipeCard.vue'

describe('SwipeCard', () => {
  it('renders profile information', () => {
    const profile = {
      id: '1',
      name: 'John',
      age: 25,
      photos: ['photo1.jpg']
    }

    const wrapper = mount(SwipeCard, {
      props: { profile },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('John')
    expect(wrapper.text()).toContain('25')
  })

  it('emits swipe event', async () => {
    const wrapper = mount(SwipeCard, {
      props: { profile: mockProfile }
    })

    await wrapper.find('.swipe-area').trigger('swipe', { direction: 'left' })
    
    expect(wrapper.emitted('swipe')).toBeTruthy()
    expect(wrapper.emitted('swipe')[0]).toEqual(['left'])
  })
})
```

## Build and Deployment

### Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          telegram: ['axios']
        }
      }
    }
  },
  server: {
    port: 3000,
    host: true
  }
})
```

### Environment Variables

```javascript
// .env.development
VITE_API_BASE_URL=http://localhost:8080/api
VITE_WS_URL=ws://localhost:8080/ws

// .env.production
VITE_API_BASE_URL=https://dating.serge.cc/api
VITE_WS_URL=wss://dating.serge.cc/ws
```

## Best Practices

### Development

1. **Use Composition API**: Prefer `<script setup>` over Options API
2. **Reactive state**: Use `ref()` for primitives, `reactive()` for objects
3. **Computed properties**: Use `computed()` for derived state
4. **Lifecycle hooks**: Use composition API lifecycle hooks
5. **Error handling**: Implement proper error boundaries
6. **Loading states**: Show loading indicators for async operations
7. **Accessibility**: Use semantic HTML and ARIA attributes

### Performance

1. **Lazy loading**: Use `defineAsyncComponent()` for heavy components
2. **Code splitting**: Split routes and components appropriately
3. **Bundle optimization**: Use Vite's built-in optimizations
4. **Image optimization**: Use appropriate image formats and sizes
5. **Caching**: Implement proper caching strategies

### Security

1. **Input validation**: Validate all user inputs
2. **XSS prevention**: Use proper data binding
3. **CSRF protection**: Use proper token handling
4. **Content Security Policy**: Implement CSP headers
5. **Dependency scanning**: Regularly update dependencies
