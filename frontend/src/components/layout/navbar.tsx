import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Sun, Moon, Package } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { useTheme } from '@/hooks/use-theme'
import { useLanguage } from '@/hooks/use-language'
import { useEffect } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const NAV_LINKS = [
  { label: 'Shop', to: '/collections' },
  { label: 'AI Scanner', to: '/scanner' },
  { label: 'Intelligence', to: '/analytics' },
]

export function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, openLogin, logout } = useAuth()
  const { cart, fetchCart } = useCart()
  const { isDark, toggle: toggleTheme } = useTheme()
  const { lang, toggleLanguage, t } = useLanguage()

  // Cart item count calculation
  const cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0

  return (
    <header className="sticky top-0 z-40 border-b border-black/[0.06] bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-6 px-4 sm:px-6 lg:px-8">
        <Link to="/" aria-label="SmartCart AI home">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn(
                  'rounded-lg px-3.5 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-black/[0.06] text-foreground'
                    : 'text-muted-foreground hover:bg-black/[0.04] hover:text-foreground',
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
          {user?.role === 'admin' && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                cn(
                  'rounded-lg px-3.5 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-black/[0.06] text-foreground'
                    : 'text-muted-foreground hover:bg-black/[0.04] hover:text-foreground',
                )
              }
            >
              Admin
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {/* Language toggle */}
          <Button
            variant="ghost"
            size="sm"
            aria-label="Switch language"
            className="text-xs font-bold font-mono px-2 py-1 h-8 text-muted-foreground hover:text-foreground"
            onClick={toggleLanguage}
          >
            {lang === 'en' ? 'EN | हिन्दी' : 'हिन्दी | EN'}
          </Button>

          {/* Dark mode toggle */}
          <Button
            variant="ghost"
            size="icon"
            aria-label="Toggle theme"
            className="text-muted-foreground focus-visible:ring-2 focus-visible:ring-primary"
            onClick={toggleTheme}
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            aria-label="Cart"
            className="text-muted-foreground relative"
            onClick={() => navigate('/checkout')}
          >
            <ShoppingCart className="h-5 w-5" />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground font-mono text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center animate-pulse">
                {cartCount}
              </span>
            )}
          </Button>

          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Account" className="text-muted-foreground p-0">
                  {user?.profile_image ? (
                    <img src={user.profile_image} alt={user.username} className="w-8 h-8 rounded-full object-cover border border-primary/20" />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center border border-primary/20 text-xs">
                      {user?.username?.slice(0, 2).toUpperCase() || 'US'}
                    </div>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="glass border border-white/10 rounded-2xl p-2 w-56 mt-2">
                <div className="px-3 py-2 text-left">
                  <p className="text-sm font-bold text-foreground truncate">
                    {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <DropdownMenuSeparator className="bg-black/[0.06]" />
                <DropdownMenuItem onClick={() => navigate('/profile')} className="rounded-xl flex items-center gap-2 py-2">
                  <User className="h-4 w-4" /> My Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/orders')} className="rounded-xl flex items-center gap-2 py-2">
                  <Package className="h-4 w-4" /> My Orders
                </DropdownMenuItem>
                {user?.role === 'admin' && (
                  <DropdownMenuItem onClick={() => navigate('/admin')} className="rounded-xl flex items-center gap-2 py-2">
                    <LayoutDashboard className="h-4 w-4" /> Admin Console
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => logout()} className="rounded-xl flex items-center gap-2 py-2 text-destructive hover:bg-destructive/10">
                  <LogOut className="h-4 w-4" /> Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Account"
              className="text-muted-foreground"
              onClick={() => openLogin()}
            >
              <User className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}