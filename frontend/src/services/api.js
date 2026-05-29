import axios from 'axios'
import { getCached, setCached, invalidateCache } from './cache'

const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE, timeout: 15000 })

let isRefreshing    = false
let refreshQueue    = []

const flushQueue = (token, error) => {
  refreshQueue.forEach(({ resolve, reject }) => error ? reject(error) : resolve(token))
  refreshQueue = []
}

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  res => res,
  async err => {
    const orig = err.config
    if (err.response?.status === 401 && !orig._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(err)
      }
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject })
        }).then(token => {
          orig.headers.Authorization = `Bearer ${token}`
          return api(orig)
        })
      }
      orig._retry   = true
      isRefreshing  = true
      try {
        const { data } = await axios.post(`${BASE}/api/auth/refresh`, { refresh_token: refreshToken })
        localStorage.setItem('access_token',  data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
        flushQueue(data.access_token, null)
        orig.headers.Authorization = `Bearer ${data.access_token}`
        return api(orig)
      } catch (refreshErr) {
        flushQueue(null, refreshErr)
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(err)
  }
)

async function cachedGet(url, params, ttlMs = 60_000) {
  const key = url + JSON.stringify(params || {})
  const hit  = getCached(key)
  if (hit) return { data: hit, fromCache: true }
  const res = await api.get(url, { params })
  setCached(key, res.data, ttlMs)
  return res
}

export const authAPI = {
  login:    (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data)            => api.post('/api/auth/register', data),
  logout:   ()                => api.post('/api/auth/logout'),
  refresh:  (token)           => api.post('/api/auth/refresh', { refresh_token: token }),
}

export const propertiesAPI = {
  list:   (params) => cachedGet('/api/properties', params, 2 * 60_000),
  get:    (id)     => cachedGet(`/api/properties/${id}`, null, 5 * 60_000),
  create: (data)   => { invalidateCache('/api/properties'); return api.post('/api/properties', data) },
  update: (id, d)  => { invalidateCache('/api/properties'); return api.put(`/api/properties/${id}`, d) },
  delete: (id)     => { invalidateCache('/api/properties'); return api.delete(`/api/properties/${id}`) },
  my:     ()       => cachedGet('/api/properties/my', null, 60_000),
  search: (q)      => cachedGet('/api/properties/search', q, 30_000),
}

export const inquiriesAPI = {
  send:  (data) => api.post('/api/inquiries', data),
  mine:  ()     => cachedGet('/api/inquiries/my', null, 30_000),
}

export const brokersAPI = {
  list: (params) => cachedGet('/api/brokers', params, 10 * 60_000),
}

export const wishlistAPI = {
  add:    (propertyId) => api.post('/api/wishlist', { property_id: propertyId }),
  remove: (propertyId) => api.delete(`/api/wishlist/${propertyId}`),
  mine:   ()           => cachedGet('/api/wishlist', null, 60_000),
}

export default api
