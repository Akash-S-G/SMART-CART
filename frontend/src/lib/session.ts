export interface User {
  id: string
  username: string
  email: string
  role: 'customer' | 'admin'
  is_active: boolean
  created_at?: string
  first_name?: string | null
  last_name?: string | null
  profile_image?: string | null
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Session {
  accessToken: string
  refreshToken: string
  user: User | null
}

const SESSION_KEY = 'smartcart.session.v1'

export function saveSession(token: TokenResponse, user: User | null): void {
  const session: Session = {
    accessToken: token.access_token,
    refreshToken: token.refresh_token,
    user,
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function updateSessionUser(user: User | null): void {
  const session = loadSession()
  if (!session) return
  localStorage.setItem(SESSION_KEY, JSON.stringify({ ...session, user }))
}

export function loadSession(): Session | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as Session
  } catch {
    return null
  }
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY)
}