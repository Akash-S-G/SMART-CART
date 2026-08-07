import { ReactNode } from 'react'
import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { Lock, LogIn } from 'lucide-react'

interface RequireAuthProps {
  children: ReactNode
  adminOnly?: boolean
}

export function RequireAuth({ children, adminOnly = false }: RequireAuthProps) {
  const { isAuthenticated, user, openLogin } = useAuth()

  if (!isAuthenticated) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-card rounded-3xl border border-border my-12 max-w-md mx-auto shadow-sm">
        <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
          <Lock className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-bold text-foreground mb-2">Authentication Required</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Please sign in to access your cart, order history, and account settings.
        </p>
        <Button onClick={() => openLogin()} className="gap-2">
          <LogIn className="h-4 w-4" /> Sign In / Register
        </Button>
      </div>
    )
  }

  if (adminOnly && user?.role !== 'admin') {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-card rounded-3xl border border-border my-12 max-w-md mx-auto shadow-sm">
        <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mb-4">
          <Lock className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-bold text-foreground mb-2">Admin Access Required</h2>
        <p className="text-sm text-muted-foreground">
          You need administrator privileges to view this management console.
        </p>
      </div>
    )
  }

  return <>{children}</>
}
