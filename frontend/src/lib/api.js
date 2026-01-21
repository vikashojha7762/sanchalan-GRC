import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    Accept: 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  // Check both 'token' and 'access_token' for compatibility
  const token = localStorage.getItem('access_token') || localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // For multipart/form-data, let axios set Content-Type automatically
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  
  return config
})

// Handle token expiration and network errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized
    // Don't redirect on login/signup endpoints - let them handle the error
    const isAuthEndpoint = error.config?.url?.includes('/auth/login') || 
                          error.config?.url?.includes('/auth/signup')
    
    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Only redirect if it's not a login/signup attempt
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/signin'
      return Promise.reject(error)
    }
    // Handle network errors
    if (error.code === 'ERR_NETWORK' || error.code === 'ERR_FAILED' || !error.response) {
      console.error('Network error:', error.message)
      console.error('Error details:', error)
      // Create a more descriptive error that includes the original error
      const networkError = new Error('Unable to connect to server. Please ensure the backend is running on http://localhost:8000')
      networkError.originalError = error
      networkError.isNetworkError = true
      return Promise.reject(networkError)
    }
    // For other errors, pass through with response data
    return Promise.reject(error)
  }
)

export default api
