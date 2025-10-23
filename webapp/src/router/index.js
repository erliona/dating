import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: () => import('../views/WelcomeView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/OnboardingView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/discovery',
    name: 'Discovery',
    component: () => import('../views/DiscoveryView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/matches',
    name: 'Matches',
    component: () => import('../views/MatchesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/likes',
    name: 'Likes',
    component: () => import('../views/LikesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/chat/:conversationId',
    name: 'Conversation',
    component: () => import('../views/ConversationView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile/edit',
    name: 'EditProfile',
    component: () => import('../views/EditProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/')
  } else if (to.name === 'Welcome' && userStore.isAuthenticated) {
    next('/discovery')
  } else {
    next()
  }
})

export default router
