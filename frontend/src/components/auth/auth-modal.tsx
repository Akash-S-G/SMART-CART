import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/use-auth'
import { loginApi, registerApi, googleLoginApi, getProfileApi } from '@/lib/api'
import { saveSession } from '@/lib/session'
import { useToast } from '@/components/ui/use-toast'
import { useCart } from '@/hooks/use-cart'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>
type RegisterFormValues = z.infer<typeof registerSchema>

export function AuthModal() {
  const { isModalOpen, closeModal, modalTab, login } = useAuth()
  const { fetchCart } = useCart()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'login' | 'register'>(modalTab)

  useEffect(() => {
    if (isModalOpen) {
      setTab(modalTab)
      loginForm.reset()
      registerForm.reset()
    }
  }, [isModalOpen, modalTab])

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const registerForm = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: '', email: '', password: '' },
  })

  const onLogin = async (data: LoginFormValues) => {
    setLoading(true)
    const payload = {
      email: data.email.trim().toLowerCase(),
      password: data.password,
    }
    try {
      const tokens = await loginApi(payload)
      saveSession(tokens, null)
      const profile = await getProfileApi()
      saveSession(tokens, profile)
      login(profile)
      fetchCart()
      toast({
        title: 'Welcome back!',
        description: `Logged in successfully as ${profile.username}`,
      })
      closeModal()
    } catch (err: any) {
      toast({
        title: 'Authentication Failed',
        description: err.message || 'Incorrect email or password.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const onRegister = async (data: RegisterFormValues) => {
    setLoading(true)
    const payload = {
      username: data.username.trim(),
      email: data.email.trim().toLowerCase(),
      password: data.password,
    }
    try {
      const tokens = await registerApi(payload)
      saveSession(tokens, null)
      const profile = await getProfileApi()
      saveSession(tokens, profile)
      login(profile)
      fetchCart()
      toast({
        title: 'Account Created!',
        description: 'Your SmartCart AI profile is ready.',
      })
      closeModal()
    } catch (err: any) {
      toast({
        title: 'Registration Failed',
        description: err.message || 'Account already exists or invalid details.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFillDemoAdmin = () => {
    loginForm.setValue('email', 'admin@smartcart.ai')
    loginForm.setValue('password', 'SmartCart@123')
    onLogin({ email: 'admin@smartcart.ai', password: 'SmartCart@123' })
  }

  const handleFillDemoCustomer = () => {
    loginForm.setValue('email', 'customer@smartcart.ai')
    loginForm.setValue('password', 'SmartCart@123')
    onLogin({ email: 'customer@smartcart.ai', password: 'SmartCart@123' })
  }

  const handleGoogleSignIn = () => {
    const clientId = '599957931306-9m17h4k22onovs62rhd2tg9flkuruhsh.apps.googleusercontent.com'
    const redirectUri = window.location.origin
    const scope = 'openid email profile'
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scope)}&prompt=select_account`
    window.location.href = authUrl
  }

  const handleMockGoogleSignIn = async () => {
    setLoading(true)
    try {
      const googleUsers = [
        {
          email: 'admin.google@gmail.com', // Starts with admin -> assigns admin role!
          username: 'admin_google_dev',
          first_name: 'Admin Google',
          last_name: 'Developer',
          profile_image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
        },
        {
          email: 'alex.google@gmail.com',
          username: 'alex_google_shopper',
          first_name: 'Alex',
          last_name: 'Mercer',
          profile_image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=facearea&facepad=2.25&w=256&h=256&q=80',
        },
      ]

      const selectedGoogleUser = googleUsers[Math.floor(Math.random() * googleUsers.length)]

      const tokens = await googleLoginApi(selectedGoogleUser)
      saveSession(tokens, null)
      const profile = await getProfileApi()
      saveSession(tokens, profile)
      login(profile)
      fetchCart()
      toast({
        title: 'Mock Google Sign In Successful',
        description: `Logged in as ${profile.username} (${profile.email})`,
      })
      closeModal()
    } catch (err: any) {
      toast({
        title: 'Google Auth Failed',
        description: err.message || 'Unable to connect to Google.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isModalOpen} onOpenChange={(open) => !open && closeModal()}>
      <DialogContent className="glass max-w-[420px] rounded-3xl border border-white/10 shadow-2xl p-6">
        <DialogHeader className="text-center">
          <DialogTitle className="text-2xl font-bold tracking-tight text-foreground">
            SmartCart AI
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-sm mt-1">
            Access secure payments, scanner history, and AI insights.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={tab} onValueChange={(v) => setTab(v as any)} className="w-full mt-6">
          <TabsList className="grid grid-cols-2 bg-black/[0.04] p-1 rounded-xl">
            <TabsTrigger value="login" className="rounded-lg py-2 text-sm font-medium">
              Sign In
            </TabsTrigger>
            <TabsTrigger value="register" className="rounded-lg py-2 text-sm font-medium">
              Sign Up
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="mt-4">
            <form onSubmit={loginForm.handleSubmit(onLogin)} className="space-y-4">
              <div>
                <Label htmlFor="login-email" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                  Email Address
                </Label>
                <Input
                  id="login-email"
                  type="email"
                  placeholder="name@example.com"
                  className="mt-1.5 bg-card/50 border border-black/10 rounded-xl py-5"
                  {...loginForm.register('email')}
                />
                {loginForm.formState.errors.email && (
                  <p className="text-xs text-destructive mt-1">{loginForm.formState.errors.email.message}</p>
                )}
              </div>

              <div>
                <div className="flex justify-between items-center">
                  <Label htmlFor="login-pass" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                    Password
                  </Label>
                  <button type="button" className="text-xs text-secondary font-semibold hover:underline">
                    Forgot?
                  </button>
                </div>
                <Input
                  id="login-pass"
                  type="password"
                  placeholder="••••••••"
                  className="mt-1.5 bg-card/50 border border-black/10 rounded-xl py-5"
                  {...loginForm.register('password')}
                />
                {loginForm.formState.errors.password && (
                  <p className="text-xs text-destructive mt-1">{loginForm.formState.errors.password.message}</p>
                )}
              </div>

              <Button type="submit" variant="gradient" className="w-full mt-6 py-5 rounded-xl text-sm uppercase tracking-widest font-semibold" disabled={loading}>
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              {/* Quick Demo Fill Buttons */}
              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={handleFillDemoCustomer}
                  className="flex-1 py-2 px-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-xl text-[11px] font-bold transition text-center cursor-pointer"
                >
                  ⚡ Fill Customer Demo
                </button>
                <button
                  type="button"
                  onClick={handleFillDemoAdmin}
                  className="flex-1 py-2 px-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/20 rounded-xl text-[11px] font-bold transition text-center cursor-pointer"
                >
                  ⚡ Fill Admin Demo
                </button>
              </div>
            </form>

            <div className="relative flex py-4 items-center">
              <div className="flex-grow border-t border-black/[0.06]"></div>
              <span className="flex-shrink mx-4 text-muted-foreground text-[10px] uppercase font-bold tracking-wider">or continue with</span>
              <div className="flex-grow border-t border-black/[0.06]"></div>
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={handleGoogleSignIn}
              className="w-full py-5 rounded-xl border border-black/10 hover:bg-black/[0.02] text-xs font-semibold gap-2"
              disabled={loading}
            >
              <GoogleIcon className="h-4 w-4" />
              Sign in with Google
            </Button>
            <button
              type="button"
              onClick={handleMockGoogleSignIn}
              className="w-full mt-2 text-center text-[11px] text-muted-foreground hover:text-foreground hover:underline font-semibold"
              disabled={loading}
            >
              Bypass with Mock Google Account
            </button>
          </TabsContent>

          <TabsContent value="register" className="mt-4">
            <form onSubmit={registerForm.handleSubmit(onRegister)} className="space-y-4">
              <div>
                <Label htmlFor="reg-name" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                  Username
                </Label>
                <Input
                  id="reg-name"
                  placeholder="alexmercer"
                  className="mt-1.5 bg-card/50 border border-black/10 rounded-xl py-5"
                  {...registerForm.register('username')}
                />
                {registerForm.formState.errors.username && (
                  <p className="text-xs text-destructive mt-1">{registerForm.formState.errors.username.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="reg-email" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                  Email Address
                </Label>
                <Input
                  id="reg-email"
                  type="email"
                  placeholder="name@example.com"
                  className="mt-1.5 bg-card/50 border border-black/10 rounded-xl py-5"
                  {...registerForm.register('email')}
                />
                {registerForm.formState.errors.email && (
                  <p className="text-xs text-destructive mt-1">{registerForm.formState.errors.email.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="reg-pass" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                  Password
                </Label>
                <Input
                  id="reg-pass"
                  type="password"
                  placeholder="Min. 8 characters"
                  className="mt-1.5 bg-card/50 border border-black/10 rounded-xl py-5"
                  {...registerForm.register('password')}
                />
                {registerForm.formState.errors.password && (
                  <p className="text-xs text-destructive mt-1">{registerForm.formState.errors.password.message}</p>
                )}
              </div>

              <Button type="submit" variant="gradient" className="w-full mt-6 py-5 rounded-xl text-sm uppercase tracking-widest font-semibold" disabled={loading}>
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </form>

            <div className="relative flex py-4 items-center">
              <div className="flex-grow border-t border-black/[0.06]"></div>
              <span className="flex-shrink mx-4 text-muted-foreground text-[10px] uppercase font-bold tracking-wider">or continue with</span>
              <div className="flex-grow border-t border-black/[0.06]"></div>
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={handleGoogleSignIn}
              className="w-full py-5 rounded-xl border border-black/10 hover:bg-black/[0.02] text-xs font-semibold gap-2"
              disabled={loading}
            >
              <GoogleIcon className="h-4 w-4" />
              Sign up with Google
            </Button>
            <button
              type="button"
              onClick={handleMockGoogleSignIn}
              className="w-full mt-2 text-center text-[11px] text-muted-foreground hover:text-foreground hover:underline font-semibold"
              disabled={loading}
            >
              Bypass with Mock Google Account
            </button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

function GoogleIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
        fill="#EA4335"
      />
    </svg>
  )
}
