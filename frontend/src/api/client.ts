import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

// Attach token on every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global 401 handler: purge invalid/expired token and redirect
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user_email')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?expired=1'
      }
    }
    return Promise.reject(error)
  }
)

export default api

