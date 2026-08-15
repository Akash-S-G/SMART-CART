import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Sun, Moon, Package, Camera, MapPin, Search, Sparkles } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { useTheme } from '@/hooks/use-theme'
import { useLanguage } from '@/hooks/use-language'
import { useState } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const NAV_LINKS = [
  { label: 'Shop Catalog', to: '/collections' },
  { label: 'AI Scanner', to: '/scanner', icon: Camera },
  { label: 'Analytics', to: '/analytics' },
]

export function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, openLogin, logout } = useAuth()
  const { cart } = useCart()
  const { isDark, toggle: toggleTheme } = useTheme()
  const { lang, toggleLanguage } = useLanguage()
  const [navSearch, setNavSearch] = useState('')

  const cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0
  const cartTotal = cart?.items?.reduce((sum, item) => sum + (item.product?.price || 0) * item.quantity, 0) || 0

  const handleNavSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (navSearch.trim()) {
      navigate(`/collections?search=${encodeURIComponent(navSearch.trim())}`)
    }
  }

  return (
    <div className="sticky top-0 z-40 w-full shadow-xs">
      {/* Top Banner */}
      <div className="bg-primary text-primary-foreground text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2">
        <span className="inline-flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-full text-[11px] font-bold">
          ⚡ 10 MINS
        </span>
        <span>Express Delivery in Bengaluru • Free Shipping over ₹299!</span>
      </div>

      <header className="border-b border-border bg-background/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          {/* Logo & Location */}
          <div className="flex items-center gap-4 shrink-0">
            <Link to="/" aria-label="SmartCart home">
              <Logo />
            </Link>

            {/* Delivery Location badge */}
            <div className="hidden lg:flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/60 px-3 py-1.5 rounded-full border border-border/80">
              <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
              <span className="font-medium text-foreground">Indiranagar</span>
              <span className="text-[10px] text-muted-foreground">560038</span>
            </div>
          </div>

          {/* Quick Header Search */}
          <form onSubmit={handleNavSearch} className="hidden md:flex flex-1 max-w-md mx-4 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={navSearch}
              onChange={(e) => setNavSearch(e.target.value)}
              placeholder="Search groceries (e.g. Milk, Atta, Eggs)..."
              className="w-full h-9 pl-9 pr-4 text-xs bg-muted/50 border border-border rounded-full text-foreground placeholder:text-muted-foreground/70 outline-none focus:border-primary focus:bg-background transition-all"
            />
          </form>

          {/* Nav Navigation Links */}
          <nav className="hidden xl:flex items-center gap-1" aria-label="Primary">
            {NAV_LINKS.map((link) => {
              const Icon = link.icon
              return (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    cn(
                      'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )
                  }
                >
                  {Icon && <Icon className="h-3.5 w-3.5 text-primary" />}
                  {link.label}
                </NavLink>
              )
            })}
            {user?.role === 'admin' && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  cn(
                    'rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  )
                }
              >
                Admin
              </NavLink>
            )}
          </nav>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Language toggle */}
            <Button
              variant="ghost"
              size="sm"
              aria-label="Switch language"
              className="text-[11px] font-bold px-2 h-8 text-muted-foreground hover:text-foreground"
              onClick={toggleLanguage}
            >
              {lang === 'en' ? 'EN | हिन्दी' : 'हिन्दी | EN'}
            </Button>

            {/* Dark mode toggle */}
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={toggleTheme}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>

            {/* Cart Button with Count & Price */}
            <Button
              variant="default"
              size="sm"
              className="h-9 px-3 gap-2 rounded-xl bg-primary text-primary-foreground font-semibold text-xs shadow-xs hover:opacity-90"
              onClick={() => navigate('/checkout')}
            >
              <div className="relative flex items-center">
                <ShoppingCart className="h-4 w-4" />
                {cartCount > 0 && (
                  <span className="absolute -top-2 -right-2 bg-amber-400 text-black font-extrabold text-[10px] h-4 min-w-[16px] px-1 rounded-full flex items-center justify-center">
                    {cartCount}
                  </span>
                )}
              </div>
              <span className="hidden sm:inline-block font-bold">
                {cartCount > 0 ? `₹${cartTotal}` : 'Cart'}
              </span>
            </Button>

            {/* User Profile / Auth */}
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="Account" className="h-9 w-9 p-0 rounded-full">
                    {user?.profile_image ? (
                      <img src={user.profile_image} alt={user.username} className="w-8 h-8 rounded-full object-cover border border-primary/30" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center border border-primary/20 text-xs">
                        {user?.username?.slice(0, 2).toUpperCase() || 'US'}
                      </div>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-card border border-border rounded-2xl p-2 w-56 mt-2 shadow-xl">
                  <div className="px-3 py-2 text-left">
                    <p className="text-sm font-bold text-foreground truncate">
                      {user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  </div>
                  <DropdownMenuSeparator className="bg-border" />
                  <DropdownMenuItem onClick={() => navigate('/profile')} className="rounded-xl flex items-center gap-2 py-2 text-xs font-semibold cursor-pointer">
                    <User className="h-4 w-4 text-muted-foreground" /> My Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/orders')} className="rounded-xl flex items-center gap-2 py-2 text-xs font-semibold cursor-pointer">
                    <Package className="h-4 w-4 text-muted-foreground" /> My Orders
                  </DropdownMenuItem>
                  {user?.role === 'admin' && (
                    <DropdownMenuItem onClick={() => navigate('/admin')} className="rounded-xl flex items-center gap-2 py-2 text-xs font-semibold cursor-pointer">
                      <LayoutDashboard className="h-4 w-4 text-muted-foreground" /> Admin Console
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator className="bg-border" />
                  <DropdownMenuItem onClick={() => logout()} className="rounded-xl flex items-center gap-2 py-2 text-xs font-semibold text-destructive hover:bg-destructive/10 cursor-pointer">
                    <LogOut className="h-4 w-4" /> Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className="h-9 px-3 rounded-xl text-xs font-semibold border-border hover:bg-muted"
                onClick={() => openLogin()}
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </header>
    </div>
  )
}