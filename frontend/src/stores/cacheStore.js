import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useCacheStore = create(
  persist(
    (set, get) => ({
      // Cache storage
      apiCache: {},
      imageCache: {},
      whiteboardCache: {},
      model3dCache: {},

      // Cache API responses
      setApiCache: (key, data, ttlMinutes = 5) => {
        const expiresAt = Date.now() + ttlMinutes * 60 * 1000
        set((state) => ({
          apiCache: {
            ...state.apiCache,
            [key]: { data, expiresAt }
          }
        }))
      },

      getApiCache: (key) => {
        const cached = get().apiCache[key]
        if (!cached) return null
        if (Date.now() > cached.expiresAt) {
          // Expired - remove it
          set((state) => {
            const newCache = { ...state.apiCache }
            delete newCache[key]
            return { apiCache: newCache }
          })
          return null
        }
        return cached.data
      },

      // Cache images (base64)
      setImageCache: (key, base64Data) => {
        set((state) => ({
          imageCache: {
            ...state.imageCache,
            [key]: { data: base64Data, timestamp: Date.now() }
          }
        }))
      },

      getImageCache: (key) => {
        return get().imageCache[key]?.data || null
      },

      // Whiteboard cache
      saveWhiteboard: (id, drawingData) => {
        set((state) => ({
          whiteboardCache: {
            ...state.whiteboardCache,
            [id]: { data: drawingData, timestamp: Date.now() }
          }
        }))
      },

      getWhiteboard: (id) => {
        return get().whiteboardCache[id]?.data || null
      },

      getAllWhiteboards: () => {
        return Object.entries(get().whiteboardCache).map(([id, item]) => ({
          id,
          ...item
        }))
      },

      deleteWhiteboard: (id) => {
        set((state) => {
          const newCache = { ...state.whiteboardCache }
          delete newCache[id]
          return { whiteboardCache: newCache }
        })
      },

      // 3D Model cache
      save3DModel: (id, modelData) => {
        set((state) => ({
          model3dCache: {
            ...state.model3dCache,
            [id]: { data: modelData, timestamp: Date.now() }
          }
        }))
      },

      get3DModel: (id) => {
        return get().model3dCache[id]?.data || null
      },

      getAll3DModels: () => {
        return Object.entries(get().model3dCache).map(([id, item]) => ({
          id,
          ...item
        }))
      },

      delete3DModel: (id) => {
        set((state) => {
          const newCache = { ...state.model3dCache }
          delete newCache[id]
          return { model3dCache: newCache }
        })
      },

      // Clear all caches
      clearAllCaches: () => {
        set({
          apiCache: {},
          imageCache: {},
          whiteboardCache: {},
          model3dCache: {}
        })
      },

      // Get cache stats
      getCacheStats: () => {
        const state = get()
        return {
          apiCacheSize: Object.keys(state.apiCache).length,
          imageCacheSize: Object.keys(state.imageCache).length,
          whiteboardCacheSize: Object.keys(state.whiteboardCache).length,
          model3dCacheSize: Object.keys(state.model3dCache).length,
          totalSize: JSON.stringify(state).length
        }
      }
    }),
    {
      name: 'housing-platform-cache',
      partialize: (state) => ({
        apiCache: state.apiCache,
        imageCache: state.imageCache,
        whiteboardCache: state.whiteboardCache,
        model3dCache: state.model3dCache
      })
    }
  )
)
