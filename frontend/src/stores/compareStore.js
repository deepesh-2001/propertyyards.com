import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const MAX = 4

export const useCompareStore = create(
  persist(
    (set, get) => ({
      items: [], // array of property objects
      add: (p) => {
        if (!p || !p.id) return false
        const items = get().items
        if (items.find((x) => x.id === p.id)) return false
        if (items.length >= MAX) return false
        set({ items: [...items, p] })
        return true
      },
      remove: (id) => set({ items: get().items.filter((x) => x.id !== id) }),
      clear: () => set({ items: [] }),
      has: (id) => !!get().items.find((x) => x.id === id),
      max: MAX,
    }),
    { name: 'compare-store' }
  )
)
