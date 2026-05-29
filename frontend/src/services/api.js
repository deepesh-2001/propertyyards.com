import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Helpers for components that use raw fetch (e.g. file uploads, WebSockets,
// streaming). Build a fully-qualified URL against the configured origin and
// attach the bearer token when present.
export const apiUrl = (path) => `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`

export const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Authentication endpoints
export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  refresh: (refresh_token) =>
    api.post('/api/auth/refresh', { refresh_token }),
  logout: () => api.post('/api/auth/logout')
}

// User endpoints
export const userAPI = {
  getCurrentProfile: () => api.get('/api/users/me'),
  updateProfile: (data) => api.put('/api/users/me', data),
  getUserById: (userId) => api.get(`/api/users/${userId}`),
  getUserProperties: (userId, page = 1, limit = 20) =>
    api.get(`/api/users/${userId}/properties`, { params: { page, limit } })
}

// Property endpoints
export const propertyAPI = {
  listProperties: (page = 1, limit = 20, status) =>
    api.get('/api/properties', { params: { page, limit, status } }),
  searchProperties: (filters) =>
    api.get('/api/properties/search', { params: filters }),
  getPropertyById: (propertyId) => api.get(`/api/properties/${propertyId}`),
  createProperty: (data) => api.post('/api/properties', data),
  updateProperty: (propertyId, data) =>
    api.put(`/api/properties/${propertyId}`, data),
  deleteProperty: (propertyId) => api.delete(`/api/properties/${propertyId}`)
}

// Wishlist endpoints
export const wishlistAPI = {
  addToWishlist: (propertyId) =>
    api.post(`/api/properties/${propertyId}/wishlist`),
  removeFromWishlist: (propertyId) =>
    api.delete(`/api/properties/${propertyId}/wishlist`)
}

// Inquiry endpoints
export const inquiryAPI = {
  getUserInquiries: (page = 1, limit = 20) =>
    api.get('/api/inquiries', { params: { page, limit } }),
  getInquiryById: (inquiryId) => api.get(`/api/inquiries/${inquiryId}`),
  createInquiry: (data) => api.post('/api/inquiries', data),
  updateInquiry: (inquiryId, data) =>
    api.put(`/api/inquiries/${inquiryId}`, data),
  deleteInquiry: (inquiryId) => api.delete(`/api/inquiries/${inquiryId}`),
  getPropertyInquiries: (propertyId, page = 1, limit = 20) =>
    api.get(`/api/inquiries/property/${propertyId}/inquiries`, {
      params: { page, limit }
    })
}

// Admin endpoints
export const adminAPI = {
  getAnalytics: () => api.get('/api/admin/analytics'),
  getAllUsers: (page = 1, limit = 50, role) =>
    api.get('/api/admin/users', { params: { page, limit, role } }),
  getAllProperties: (page = 1, limit = 50, status) =>
    api.get('/api/admin/properties', { params: { page, limit, status } }),
  approveProperty: (propertyId) =>
    api.post(`/api/admin/properties/${propertyId}/approve`),
  rejectProperty: (propertyId, reason) =>
    api.post(`/api/admin/properties/${propertyId}/reject`, { reason }),
  deleteUser: (userId) => api.delete(`/api/admin/users/${userId}`),
  deactivateUser: (userId) =>
    api.post(`/api/admin/users/${userId}/deactivate`),
  getAuditLogs: (page = 1, limit = 50, action) =>
    api.get('/api/admin/audit-logs', { params: { page, limit, action } })
}

export default api

