import api from './api'

export const authService = {
  signup: async (data) => {
    const response = await api.post('/auth/signup', data)
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data))
    }
    return response.data
  },

  login: async (email, password, industry) => {
    const response = await api.post('/auth/login', { email, password, industry })
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data))
    }
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  getToken: () => {
    return localStorage.getItem('token')
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token')
  },
}
