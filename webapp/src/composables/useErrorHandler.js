import { ref, computed } from 'vue'

/**
 * Composable for handling standardized API errors
 */
export function useErrorHandler() {
  const errors = ref({})
  const globalError = ref(null)
  
  /**
   * Clear all errors
   */
  const clearErrors = () => {
    errors.value = {}
    globalError.value = null
  }
  
  /**
   * Set a field-specific error
   */
  const setFieldError = (field, message) => {
    errors.value[field] = message
  }
  
  /**
   * Set a global error
   */
  const setGlobalError = (message) => {
    globalError.value = message
  }
  
  /**
   * Handle API error response
   */
  const handleApiError = (error) => {
    clearErrors()
    
    if (error.response?.data?.error) {
      const errorData = error.response.data
      
      // Handle field-specific validation errors
      if (errorData.details?.field) {
        setFieldError(errorData.details.field, errorData.message)
      } else {
        setGlobalError(errorData.message)
      }
      
      // Log error for debugging
      console.error('API Error:', {
        code: errorData.code,
        message: errorData.message,
        status: error.response.status,
        timestamp: errorData.timestamp,
        request_id: errorData.request_id
      })
    } else {
      // Handle network or other errors
      setGlobalError('Network error. Please try again.')
    }
  }
  
  /**
   * Get error message for a specific field
   */
  const getFieldError = (field) => {
    return errors.value[field] || null
  }
  
  /**
   * Check if a field has an error
   */
  const hasFieldError = (field) => {
    return !!errors.value[field]
  }
  
  /**
   * Check if there are any errors
   */
  const hasErrors = computed(() => {
    return Object.keys(errors.value).length > 0 || !!globalError.value
  })
  
  /**
   * Get all error messages
   */
  const allErrors = computed(() => {
    const fieldErrors = Object.values(errors.value)
    const globalErrors = globalError.value ? [globalError.value] : []
    return [...fieldErrors, ...globalErrors]
  })
  
  /**
   * Get error summary for display
   */
  const errorSummary = computed(() => {
    if (globalError.value) {
      return globalError.value
    }
    
    const fieldErrors = Object.entries(errors.value)
    if (fieldErrors.length === 1) {
      return fieldErrors[0][1]
    } else if (fieldErrors.length > 1) {
      return `${fieldErrors.length} validation errors`
    }
    
    return null
  })
  
  return {
    errors,
    globalError,
    clearErrors,
    setFieldError,
    setGlobalError,
    handleApiError,
    getFieldError,
    hasFieldError,
    hasErrors,
    allErrors,
    errorSummary
  }
}

/**
 * Composable for handling specific error types
 */
export function useErrorTypes() {
  /**
   * Check if error is authentication related
   */
  const isAuthError = (error) => {
    return error.response?.data?.code?.startsWith('AUTH_')
  }
  
  /**
   * Check if error is validation related
   */
  const isValidationError = (error) => {
    return error.response?.data?.code?.startsWith('VAL_')
  }
  
  /**
   * Check if error is rate limit related
   */
  const isRateLimitError = (error) => {
    return error.response?.data?.code?.startsWith('RATE_')
  }
  
  /**
   * Check if error is business logic related
   */
  const isBusinessError = (error) => {
    return error.response?.data?.code?.startsWith('BIZ_')
  }
  
  /**
   * Check if error is system related
   */
  const isSystemError = (error) => {
    return error.response?.data?.code?.startsWith('SYS_')
  }
  
  /**
   * Get user-friendly error message
   */
  const getUserFriendlyMessage = (error) => {
    if (!error.response?.data) {
      return 'Network error. Please check your connection.'
    }
    
    const errorData = error.response.data
    const code = errorData.code
    
    switch (code) {
      case 'AUTH_001':
        return 'Please log in to continue.'
      case 'AUTH_002':
        return 'Your session has expired. Please log in again.'
      case 'AUTH_003':
        return 'Invalid authentication token.'
      case 'AUTH_004':
        return 'You do not have permission to perform this action.'
      case 'VAL_001':
        return 'Please check your input and try again.'
      case 'VAL_002':
        return 'Required field is missing.'
      case 'VAL_003':
        return 'Invalid format provided.'
      case 'BIZ_001':
        return 'The requested resource was not found.'
      case 'BIZ_002':
        return 'This resource already exists.'
      case 'BIZ_003':
        return 'This action is not allowed.'
      case 'RATE_001':
        return 'Too many requests. Please wait a moment and try again.'
      case 'SYS_001':
        return 'Something went wrong. Please try again later.'
      case 'SYS_002':
        return 'Service is temporarily unavailable.'
      default:
        return errorData.message || 'An unexpected error occurred.'
    }
  }
  
  return {
    isAuthError,
    isValidationError,
    isRateLimitError,
    isBusinessError,
    isSystemError,
    getUserFriendlyMessage
  }
}
