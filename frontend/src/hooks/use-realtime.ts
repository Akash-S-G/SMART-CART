import { useEffect, useRef } from 'react'
import { realtime, type RealtimeEvent } from '@/lib/realtime'

export function useRealtime(
  topics: string[],
  listener: (event: RealtimeEvent) => void,
): void {
  const listenerRef = useRef(listener)
  const topicsRef = useRef(topics)
  const key = topics.join('|')

  useEffect(() => {
    listenerRef.current = listener
    topicsRef.current = topics
  })

  useEffect(() => {
    return realtime.subscribe(topicsRef.current, (event) => {
      listenerRef.current(event)
    })
  }, [key])
}
