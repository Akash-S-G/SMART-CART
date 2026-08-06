import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { API_BASE_URL } from '@/lib/env'
import { clearSession, loadSession, saveSession } from '@/lib/session'
import type { TokenResponse } from '@/types/api'

export interface ApiErrorShape {
  message?: string
  detail?: unknown
  status?: number
}

export class ApiError extends Error {
  status: number | null
  detail: unknown
  constructor(message: string, status: number | null = null, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export const http = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

let refreshPromise: Promise<string | null> | null = null

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const session = loadSession()
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`
  }
  return config
})

async function refreshAccessToken() {
  const session = loadSession()
  if (!session?.refreshToken) {
    clearSession()
    return null
  }
  if (!refreshPromise) {
    refreshPromise = axios
      .post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: session.refreshToken,
      })
      .then((response) => {
        saveSession(response.data, session.user)
        return response.data.access_token
      })
      .catch(() => {
        clearSession()
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalRequest = error.config

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      const token = await refreshAccessToken()
      if (token) {
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${token}`,
        }
        return http.request(originalRequest)
      }
    }
    return Promise.reject(error)
  },
)

function extractMessage(error: unknown, fallback: string): ApiError {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string | Record<string, unknown> } | undefined
    const status = error.response?.status ?? null
    if (typeof data?.detail === 'string') return new ApiError(data.detail, status, data.detail)
    if (data?.detail && typeof data.detail === 'object') {
      return new ApiError('Validation failed', status, data.detail)
    }
    if (error.code === 'ECONNABORTED') return new ApiError('Request timed out', status)
    return new ApiError(error.message, status)
  }
  if (error instanceof Error) return new ApiError(error.message)
  return new ApiError(fallback)
}

export async function getJson<T>(url: string, fallback?: string): Promise<T> {
  try {
    const response = await http.get<T>(url)
    return response.data
  } catch (error) {
    throw extractMessage(error, fallback ?? `Failed to load ${url}`)
  }
}

export async function postJson<T, Body = unknown>(url: string, body?: Body, fallback?: string): Promise<T> {
  try {
    const response = await http.post<T>(url, body)
    return response.data
  } catch (error) {
    throw extractMessage(error, fallback ?? `Request failed`)
  }
}

export async function putJson<T, Body = unknown>(url: string, body?: Body, fallback?: string): Promise<T> {
  try {
    const response = await http.put<T>(url, body)
    return response.data
  } catch (error) {
    throw extractMessage(error, fallback ?? `Update failed`)
  }
}

export async function patchJson<T, Body = unknown>(url: string, body?: Body, fallback?: string): Promise<T> {
  try {
    const response = await http.patch<T>(url, body)
    return response.data
  } catch (error) {
    throw extractMessage(error, fallback ?? `Update failed`)
  }
}

export async function deleteJson<T>(url: string, fallback?: string): Promise<T> {
  try {
    const response = await http.delete<T>(url)
    return response.data
  } catch (error) {
    throw extractMessage(error, fallback ?? `Delete failed`)
  }
}