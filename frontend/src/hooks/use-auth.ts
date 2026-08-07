import { create } from 'zustand'
import { loadSession, updateSessionUser, clearSession as clearSessionHelper, type User } from '@/lib/session'
import { getProfileApi } from '@/lib/api'

interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isModalOpen: boolean
  modalTab: 'login' | 'register'
  openLogin: () => void
  openRegister: () => void
  closeModal: () => void
  login: (user: User) => void
  logout: () => void
  fetchProfile: () => Promise<User | null>
}

export const useAuth = create<AuthStore>((set) => {
  const session = loadSession()
  return {
    user: session?.user || null,
    isAuthenticated: !!session?.accessToken,
    isModalOpen: false,
    modalTab: 'login',

    openLogin: () => set({ isModalOpen: true, modalTab: 'login' }),
    openRegister: () => set({ isModalOpen: true, modalTab: 'register' }),
    closeModal: () => set({ isModalOpen: false }),

    login: (user) => set({ user, isAuthenticated: true, isModalOpen: false }),
    logout: () => {
      clearSessionHelper()
      set({ user: null, isAuthenticated: false })
    },

    fetchProfile: async () => {
      const s = loadSession()
      if (!s?.accessToken) return null
      try {
        const u = await getProfileApi()
        updateSessionUser(u)
        set({ user: u, isAuthenticated: true })
        return u
      } catch {
        return null
      }
    },
  }
})
