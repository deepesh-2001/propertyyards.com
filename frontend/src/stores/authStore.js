import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI } from '../services/api'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      register: async (userData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.register(userData)
          // Auto-login after registration
          const loginResponse = await authAPI.login({
            email: userData.email,
            password: userData.password
          })
          set({
            user: loginResponse.data,
            accessToken: loginResponse.data.access_token,
            refreshToken: loginResponse.data.refresh_token,
            isAuthenticated: true,
            isLoading: false
          })
          localStorage.setItem(
            'access_token',
            loginResponse.data.access_token
          )
          localStorage.setItem(
            'refresh_token',
            loginResponse.data.refresh_token
          )
          return loginResponse.data
        } catch (error) {
          const errorMessage =
            error.response?.data?.detail || error.message || 'Registration failed'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.login(credentials)
          set({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
          return response.data
        } catch (error) {
          const errorMessage =
            error.response?.data?.detail || error.message || 'Login failed'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authAPI.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false
          })
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      },

      refreshAccessToken: async () => {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) return false

        try {
          const response = await authAPI.refresh(refreshToken)
          set({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token
          })
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
          return true
        } catch (error) {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false
          })
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          return false
        }
      },

      setUser: (user) => set({ user }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null })
    }),
    {
      name: 'auth-storage',
      // Only persist specific fields
      partialize: (state) => ({
        accessToken:state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

