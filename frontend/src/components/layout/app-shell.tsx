import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Outlet, useSearchParams, useLocation } from 'react-router-dom'
import { Navbar } from '@/components/layout/navbar'
import { Footer } from '@/components/layout/footer'
import { AuthModal } from '@/components/auth/auth-modal'
import { googleLoginApi, getProfileApi } from '@/lib/api'
import { saveSession } from '@/lib/session'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { useToast } from '@/components/ui/use-toast'
import { Loader2 } from 'lucide-react'

import { useRef } from 'react'

import { AICopilot } from '@/components/ai/ai-copilot'

export function AppShell() {
  const { pathname } = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [authChecking, setAuthChecking] = useState(false)
  const { login, isAuthenticated, user, fetchProfile } = useAuth()
  const { fetchCart } = useCart()
  const { toast } = useToast()
  const processedCodeRef = useRef<string | null>(null)

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [pathname])

  useEffect(() => {
    if (isAuthenticated) {
      if (!user) fetchProfile()
      fetchCart()
    }
  }, [isAuthenticated, user])

  useEffect(() => {
    const code = searchParams.get('code')
    if (code && processedCodeRef.current !== code) {
      processedCodeRef.current = code
      // Immediately strip the code parameter from the browser URL bar
      window.history.replaceState({}, document.title, window.location.pathname)
      setSearchParams({}, { replace: true })

      setAuthChecking(true)
      const exchangeCode = async () => {
        try {
          const redirectUri = window.location.origin
          const tokens = await googleLoginApi({ code, redirect_uri: redirectUri })
          saveSession(tokens, null)
          const profile = await getProfileApi()
          saveSession(tokens, profile)
          login(profile)
          fetchCart()
          toast({
            title: 'Welcome Back!',
            description: `Signed in as ${profile.first_name || profile.username || profile.email}`,
          })
        } catch {
          toast({
            title: 'Google Login Failed',
            description: 'Could not complete Google authentication.',
            variant: 'destructive',
          })
        } finally {
          setAuthChecking(false)
        }
      }
      exchangeCode()
    }
  }, [searchParams])

  if (authChecking) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-sm font-semibold text-muted-foreground">Authenticating with Google...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="noise relative flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <AuthModal />
      <AICopilot />
    </div>
  )
}

export function PageSection({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return <section className={className}>{children}</section>
}