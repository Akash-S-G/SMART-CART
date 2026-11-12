import { WS_BASE_URL } from '@/lib/env'
import { refreshAccessToken } from '@/lib/http'
import { loadSession } from '@/lib/session'

export interface RealtimeEvent {
  type: string
  topic?: string
  data?: unknown
  ts?: string
}

type Listener = (event: RealtimeEvent) => void

interface Subscription {
  topics: Set<string>
  listener: Listener
}

const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const HEARTBEAT_CHECK_MS = 20_000
const SERVER_SILENCE_MS = 70_000
const AUTH_CLOSE_CODES = new Set([4401, 4403])

class RealtimeClient {
  private socket: WebSocket | null = null
  private subscriptions = new Set<Subscription>()
  private topicRefs = new Map<string, number>()
  private reconnectAttempt = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private lastMessageAt = 0
  private connecting = false
  private authRetryPending = false

  subscribe(topics: string[], listener: Listener): () => void {
    const subscription: Subscription = {
      topics: new Set(topics.filter(Boolean)),
      listener,
    }
    this.subscriptions.add(subscription)
    for (const topic of subscription.topics) {
      this.topicRefs.set(topic, (this.topicRefs.get(topic) ?? 0) + 1)
    }
    this.ensureConnected()
    this.sendSubscriptions([...subscription.topics])

    return () => {
      if (!this.subscriptions.delete(subscription)) return
      for (const topic of subscription.topics) {
        const count = (this.topicRefs.get(topic) ?? 1) - 1
        if (count <= 0) {
          this.topicRefs.delete(topic)
          this.send({ type: 'unsubscribe', topics: [topic] })
        } else {
          this.topicRefs.set(topic, count)
        }
      }
      if (this.subscriptions.size === 0) this.teardown()
    }
  }

  private ensureConnected(): void {
    if (this.socket || this.connecting || typeof window === 'undefined') return
    this.connecting = true

    let socket: WebSocket
    try {
      const session = loadSession()
      const protocols = session?.accessToken
        ? [`bearer.${session.accessToken}`]
        : undefined
      socket = new WebSocket(this.buildUrl(), protocols)
    } catch {
      this.connecting = false
      this.scheduleReconnect()
      return
    }
    this.socket = socket

    socket.onopen = () => {
      this.connecting = false
      this.reconnectAttempt = 0
      this.authRetryPending = false
      this.lastMessageAt = Date.now()
      this.startHeartbeat()
      this.sendSubscriptions([...this.topicRefs.keys()])
    }

    socket.onmessage = (event) => {
      this.lastMessageAt = Date.now()
      let payload: RealtimeEvent
      try {
        payload = JSON.parse(String(event.data)) as RealtimeEvent
      } catch {
        return
      }
      if (payload.type === 'PING') {
        this.send({ type: 'pong' })
        return
      }
      for (const subscription of [...this.subscriptions]) {
        if (payload.topic && !subscription.topics.has(payload.topic)) continue
        try {
          subscription.listener(payload)
        } catch {
          continue
        }
      }
    }

    socket.onerror = () => {
      socket.close()
    }

    socket.onclose = (event) => {
      this.connecting = false
      if (this.socket === socket) this.socket = null
      this.stopHeartbeat()

      if (event.code === 4401 && !this.authRetryPending) {
        this.authRetryPending = true
        void this.reauthenticate()
        return
      }
      if (AUTH_CLOSE_CODES.has(event.code)) {
        this.authRetryPending = false
        for (const subscription of [...this.subscriptions]) {
          subscription.listener({
            type: 'AUTH_ERROR',
            data: { code: event.code, reason: event.reason },
          })
        }
        return
      }
      if (this.subscriptions.size > 0) this.scheduleReconnect()
    }
  }

  private async reauthenticate(): Promise<void> {
    const token = await refreshAccessToken()
    if (token) {
      this.reconnectAttempt = 0
      this.ensureConnected()
      return
    }
    this.authRetryPending = false
    for (const subscription of [...this.subscriptions]) {
      subscription.listener({
        type: 'AUTH_ERROR',
        data: { code: 4401, reason: 'session expired' },
      })
    }
  }

  private buildUrl(): string {
    return new URL(WS_BASE_URL, window.location.origin).toString()
  }

  private send(payload: unknown): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) return false
    try {
      this.socket.send(JSON.stringify(payload))
      return true
    } catch {
      return false
    }
  }

  private sendSubscriptions(topics: string[]): void {
    if (topics.length === 0) return
    this.send({ type: 'subscribe', topics })
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer || this.subscriptions.size === 0) return
    const delay = Math.min(
      RECONNECT_MAX_MS,
      RECONNECT_BASE_MS * 2 ** this.reconnectAttempt,
    )
    const jitter = Math.floor(Math.random() * 500)
    this.reconnectAttempt += 1
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.ensureConnected()
    }, delay + jitter)
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (Date.now() - this.lastMessageAt > SERVER_SILENCE_MS) {
        this.socket?.close()
      }
    }, HEARTBEAT_CHECK_MS)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private teardown(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.reconnectAttempt = 0
    this.stopHeartbeat()
    const socket = this.socket
    this.socket = null
    this.connecting = false
    if (socket && socket.readyState < WebSocket.CLOSING) {
      socket.close(1000, 'client teardown')
    }
  }
}

export const realtime = new RealtimeClient()
