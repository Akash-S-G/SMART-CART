import { useEffect, useState } from 'react'

const KEY = 'smartcart_recent'
const MAX = 8

export function useRecent() {
  const [ids, setIds] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(KEY)
      return raw ? JSON.parse(raw) : []
    } catch { return [] }
  })

  const add = (id: string) => {
    setIds(prev => {
      const next = [id, ...prev.filter(x => x !== id)].slice(0, MAX)
      try { localStorage.setItem(KEY, JSON.stringify(next)) } catch {}
      return next
    })
  }

  return { ids, add }
}

export function useRecentlyViewedSync(productId: string | undefined) {
  const { add } = useRecent()
  useEffect(() => {
    if (productId) add(productId)
  }, [productId])
}
