import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authAPI = {
  login:    (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data)            => api.post('/api/auth/register', data),
  logout:   ()                => api.post('/api/auth/logout'),
}

export const propertiesAPI = {
  list:   (params) => api.get('/api/properties', { params }),
  get:    (id)     => api.get(`/api/properties/${id}`),
  create: (data)   => api.post('/api/properties', data),
  update: (id, d)  => api.put(`/api/properties/${id}`, d),
  delete: (id)     => api.delete(`/api/properties/${id}`),
  my:     ()       => api.get('/api/properties/my'),
}

export const inquiriesAPI = {
  send:  (data) => api.post('/api/inquiries', data),
  mine:  ()     => api.get('/api/inquiries/my'),
}

export const brokersAPI = {
  list: (params) => api.get('/api/brokers', { params }),
}

export default api
