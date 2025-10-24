import { useRouter } from 'vue-router'

/**
 * Composable for handling navigation in the application.
 * Provides consistent navigation methods across the app.
 */
export function useNavigation() {
  const router = useRouter()
  
  /**
   * Navigate to home page
   */
  const goHome = () => {
    router.push('/')
  }
  
  /**
   * Navigate to login page
   */
  const goToLogin = () => {
    router.push('/login')
  }
  
  /**
   * Navigate to profile page
   */
  const goToProfile = () => {
    router.push('/profile')
  }
  
  /**
   * Navigate to discovery page
   */
  const goToDiscovery = () => {
    router.push('/discovery')
  }
  
  /**
   * Navigate to chat page
   */
  const goToChat = () => {
    router.push('/chat')
  }
  
  /**
   * Navigate to settings page
   */
  const goToSettings = () => {
    router.push('/settings')
  }
  
  /**
   * Navigate to onboarding page
   */
  const goToOnboarding = () => {
    router.push('/onboarding')
  }
  
  /**
   * Navigate back to previous page
   */
  const goBack = () => {
    router.go(-1)
  }
  
  /**
   * Navigate to a specific route
   */
  const navigateTo = (route) => {
    if (typeof route === 'string') {
      router.push(route)
    } else {
      router.push(route)
    }
  }
  
  /**
   * Replace current route (no history entry)
   */
  const replaceRoute = (route) => {
    if (typeof route === 'string') {
      router.replace(route)
    } else {
      router.replace(route)
    }
  }
  
  /**
   * Check if current route matches pattern
   */
  const isCurrentRoute = (route) => {
    return router.currentRoute.value.path === route
  }
  
  /**
   * Get current route information
   */
  const getCurrentRoute = () => {
    return router.currentRoute.value
  }
  
  /**
   * Handle authentication redirect
   * Redirects to login if not authenticated, otherwise to intended destination
   */
  const handleAuthRedirect = (intendedRoute = '/') => {
    const token = localStorage.getItem('jwt_token')
    if (!token) {
      // Store intended route for after login
      localStorage.setItem('intended_route', intendedRoute)
      goToLogin()
    } else {
      navigateTo(intendedRoute)
    }
  }
  
  /**
   * Handle post-login redirect
   * Redirects to intended route after successful login
   */
  const handlePostLoginRedirect = () => {
    const intendedRoute = localStorage.getItem('intended_route') || '/'
    localStorage.removeItem('intended_route')
    navigateTo(intendedRoute)
  }
  
  /**
   * Handle logout redirect
   * Clears token and redirects to home
   */
  const handleLogoutRedirect = () => {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('intended_route')
    goHome()
  }
  
  /**
   * Handle 401 authentication error
   * Clears token and redirects appropriately
   */
  const handleAuthError = () => {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('intended_route')
    
    // If on a protected route, redirect to login
    const currentRoute = getCurrentRoute()
    const protectedRoutes = ['/profile', '/discovery', '/chat', '/settings']
    const isProtectedRoute = protectedRoutes.some(route => 
      currentRoute.path.startsWith(route)
    )
    
    if (isProtectedRoute) {
      goToLogin()
    } else {
      goHome()
    }
  }
  
  return {
    // Navigation methods
    goHome,
    goToLogin,
    goToProfile,
    goToDiscovery,
    goToChat,
    goToSettings,
    goToOnboarding,
    goBack,
    navigateTo,
    replaceRoute,
    
    // Route information
    isCurrentRoute,
    getCurrentRoute,
    
    // Authentication handling
    handleAuthRedirect,
    handlePostLoginRedirect,
    handleLogoutRedirect,
    handleAuthError
  }
}
