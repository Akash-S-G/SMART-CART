import { create } from 'zustand'
import { getWishlistApi, addWishlistApi, removeWishlistApi } from '@/lib/api'

interface WishlistStore {
  items: string[]
  toggleItem: (id: string) => Promise<void>
  hasItem: (id: string) => boolean
  fetchWishlist: () => Promise<void>
}

export const useWishlist = create<WishlistStore>((set, get) => {
  const loadWishlist = () => {
    try {
      const raw = localStorage.getItem('smartcart.wishlist.v1')
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  return {
    items: loadWishlist(),
    fetchWishlist: async () => {
      try {
        const data = await getWishlistApi()
        if (Array.isArray(data)) {
          const ids = data.map((item: any) => item.id)
          localStorage.setItem('smartcart.wishlist.v1', JSON.stringify(ids))
          set({ items: ids })
        }
      } catch {
        // Fallback to local state if unauthorized or offline
      }
    },
    toggleItem: async (id) => {
      const current = get().items
      const exists = current.includes(id)
      const next = exists ? current.filter((x) => x !== id) : [...current, id]
      localStorage.setItem('smartcart.wishlist.v1', JSON.stringify(next))
      set({ items: next })

      try {
        if (exists) {
          await removeWishlistApi(id)
        } else {
          await addWishlistApi(id)
        }
      } catch {
        // Keeps client UI responsive
      }
    },
    hasItem: (id) => get().items.includes(id),
  }
})
