import { create } from 'zustand'
import {
  getCartApi,
  addToCartApi,
  updateCartItemApi,
  removeCartItemApi,
  clearCartApi,
} from '@/lib/api'
import type { Cart } from '@/types/api'
import { loadSession } from '@/lib/session'

interface CartStore {
  cart: Cart | null
  loading: boolean
  error: string | null
  fetchCart: () => Promise<Cart | null>
  addItem: (productId: string, quantity?: number) => Promise<Cart | null>
  updateItem: (productId: string, quantity: number) => Promise<Cart | null>
  removeItem: (productId: string) => Promise<Cart | null>
  clearCart: () => Promise<void>
  setCart: (cart: Cart | null) => void
}

export const useCart = create<CartStore>((set, get) => ({
  cart: null,
  loading: false,
  error: null,

  setCart: (cart) => set({ cart }),

  fetchCart: async () => {
    const session = loadSession()
    if (!session?.accessToken) {
      set({ cart: null })
      return null
    }
    set({ loading: true, error: null })
    try {
      const cart = await getCartApi()
      set({ cart, loading: false })
      return cart
    } catch (err: any) {
      if (err.response?.status === 401) {
        set({ cart: null, loading: false })
        return null
      }
      set({ error: err.message || 'Failed to fetch cart', loading: false })
      return null
    }
  },

  addItem: async (productId: string, quantity = 1) => {
    const session = loadSession()
    if (!session?.accessToken) {
      const { openLogin } = await import('@/hooks/use-auth').then((m) => ({ openLogin: m.useAuth.getState().openLogin }))
      openLogin()
      const err = new Error('Please sign in to add items to your cart.')
      set({ error: err.message, loading: false })
      throw err
    }
    set({ loading: true, error: null })
    try {
      const cart = await addToCartApi(productId, quantity)
      set({ cart, loading: false })
      return cart
    } catch (err: any) {
      if (err.response?.status === 401) {
        const { openLogin } = await import('@/hooks/use-auth').then((m) => ({ openLogin: m.useAuth.getState().openLogin }))
        openLogin()
      }
      set({ error: err.message || 'Failed to add item', loading: false })
      throw err
    }
  },

  updateItem: async (productId: string, quantity: number) => {
    set({ loading: true, error: null })
    try {
      const cart = await updateCartItemApi(productId, quantity)
      set({ cart, loading: false })
      return cart
    } catch (err: any) {
      set({ error: err.message || 'Failed to update quantity', loading: false })
      throw err
    }
  },

  removeItem: async (productId: string) => {
    set({ loading: true, error: null })
    try {
      const cart = await removeCartItemApi(productId)
      set({ cart, loading: false })
      return cart
    } catch (err: any) {
      set({ error: err.message || 'Failed to remove item', loading: false })
      throw err
    }
  },

  clearCart: async () => {
    set({ loading: true, error: null })
    try {
      await clearCartApi()
      set({ cart: null, loading: false })
    } catch (err: any) {
      set({ error: err.message || 'Failed to clear cart', loading: false })
      throw err
    }
  },
}))
