function readEnv(key: 'VITE_API_URL' | 'VITE_WS_URL', fallback: string) {
  const value = import.meta.env[key]
  return typeof value === 'string' && value.length > 0 ? value : fallback
}

export const API_BASE_URL = readEnv('VITE_API_URL', '/api')
export const WS_BASE_URL = readEnv('VITE_WS_URL', 'ws://localhost:8000/ws')
