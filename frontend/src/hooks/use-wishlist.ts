import { create } from 'zustand'

interface WishlistStore {
  items: string[]
  toggleItem: (id: string) => void
  hasItem: (id: string) => boolean
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
    toggleItem: (id) => {
      const current = get().items
      const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id]
      localStorage.setItem('smartcart.wishlist.v1', JSON.stringify(next))
      set({ items: next })
    },
    hasItem: (id) => get().items.includes(id),
  }
})
