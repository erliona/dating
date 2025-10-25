import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

// Lazy loading with error handling and loading states
const lazyLoad = (componentName) => {
  return () => import(/* webpackChunkName: "views" */ `../views/${componentName}.vue`)
}

// Lazy loading with retry mechanism
const lazyLoadWithRetry = (componentName, retries = 3) => {
  return () => import(/* webpackChunkName: "views" */ `../views/${componentName}.vue`)
    .catch(error => {
      if (retries > 0) {
        console.warn(`Failed to load ${componentName}, retrying... (${retries} attempts left)`)
        return lazyLoadWithRetry(componentName, retries - 1)()
      }
      console.error(`Failed to load ${componentName} after ${retries} retries:`, error)
      throw error
    })
}

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: lazyLoad('WelcomeView'),
    meta: { requiresAuth: false }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: lazyLoadWithRetry('OnboardingView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/discovery',
    name: 'Discovery',
    component: lazyLoadWithRetry('DiscoveryView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/matches',
    name: 'Matches',
    component: lazyLoad('MatchesView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/likes',
    name: 'Likes',
    component: lazyLoad('LikesView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: lazyLoadWithRetry('ChatView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:conversationId',
    name: 'Conversation',
    component: lazyLoadWithRetry('ConversationView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: lazyLoad('ProfileView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile/edit',
    name: 'EditProfile',
    component: lazyLoad('EditProfileView'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: lazyLoad('SettingsView'),
    meta: { requiresAuth: true }
  },
  // Admin routes - lazy loaded with admin chunk
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminLogin.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/photos',
    name: 'AdminPhotos',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminPhotos.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/verifications',
    name: 'AdminVerifications',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminVerifications.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/reports',
    name: 'AdminReports',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminReports.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/moderation',
    name: 'AdminModeration',
    component: () => import(/* webpackChunkName: "admin" */ '../views/AdminModeration.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Enable scroll behavior for better UX
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const adminToken = localStorage.getItem('admin_token')
  
  // Admin routes
  if (to.meta.requiresAdmin) {
    if (!adminToken) {
      next('/admin/login')
    } else {
      next()
    }
  }
  // Regular auth routes
  else if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/')
  } else if (to.name === 'Welcome' && userStore.isAuthenticated) {
    next('/discovery')
  } else {
    next()
  }
})

export default router
