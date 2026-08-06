import { create } from 'zustand'
import { loadSession, clearSession as clearSessionHelper, type User } from '@/lib/session'

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
  }
})
