import { createRouter, createWebHistory } from 'vue-router'

const AdminDashboard = () => import('../views/AdminDashboard.vue')
const AdminUsers = () => import('../views/AdminUsers.vue')
const AdminPhotos = () => import('../views/AdminPhotos.vue')
const AdminVerifications = () => import('../views/AdminVerifications.vue')
const AdminReports = () => import('../views/AdminReports.vue')

const routes = [
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: AdminUsers,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/photos',
    name: 'AdminPhotos',
    component: AdminPhotos,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/verifications',
    name: 'AdminVerifications',
    component: AdminVerifications,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/reports',
    name: 'AdminReports',
    component: AdminReports,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Admin authentication guard
router.beforeEach((to, from, next) => {
  const adminToken = localStorage.getItem('admin_token')
  
  if (to.meta.requiresAdmin && !adminToken) {
    // Redirect to admin login
    next('/admin/login')
  } else {
    next()
  }
})

export default router
