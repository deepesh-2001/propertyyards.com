import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useSavedSearchStore = create(
  persist(
    (set, get) => ({
      searches: [], // [{id, name, filters, alerts: {email, whatsapp}, createdAt}]
      add: (search) => {
        const item = {
          id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2),
          name: search.name || `Search ${get().searches.length + 1}`,
          filters: search.filters || {},
          alerts: search.alerts || { email: true, whatsapp: false },
          createdAt: new Date().toISOString(),
        }
        set({ searches: [item, ...get().searches] })
        // best-effort sync to backend
        fetch('/api/saved-searches', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
          body: JSON.stringify(item),
        }).catch(() => null)
        return item
      },
      remove: (id) => {
        set({ searches: get().searches.filter((s) => s.id !== id) })
        fetch(`/api/saved-searches/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
        }).catch(() => null)
      },
      updateAlerts: (id, alerts) => {
        set({
          searches: get().searches.map((s) =>
            s.id === id ? { ...s, alerts: { ...s.alerts, ...alerts } } : s
          ),
        })
      },
    }),
    { name: 'saved-search-store' }
  )
)
