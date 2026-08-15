import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Sun, Moon, Package, Camera, MapPin, Search, Navigation, Check, X, Loader2 } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { useTheme } from '@/hooks/use-theme'
import { useLanguage } from '@/hooks/use-language'
import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
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

const POPULAR_LOCATIONS = [
  { area: 'Indiranagar', city: 'Bengaluru', pincode: '560038' },
  { area: 'Koramangala', city: 'Bengaluru', pincode: '560034' },
  { area: 'HSR Layout', city: 'Bengaluru', pincode: '560102' },
  { area: 'Whitefield', city: 'Bengaluru', pincode: '560066' },
  { area: 'Jayanagar', city: 'Bengaluru', pincode: '560041' },
  { area: 'Bandra West', city: 'Mumbai', pincode: '400050' },
  { area: 'Connaught Place', city: 'New Delhi', pincode: '110001' },
]

export function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, openLogin, logout } = useAuth()
  const { cart } = useCart()
  const { isDark, toggle: toggleTheme } = useTheme()
  const { lang, toggleLanguage } = useLanguage()
  const { toast } = useToast()

  const [navSearch, setNavSearch] = useState('')
  const [showLocationModal, setShowLocationModal] = useState(false)
  const [locSearch, setLocSearch] = useState('')
  const [detectingGps, setDetectingGps] = useState(false)

  // Location state with localStorage persistence
  const [currentLoc, setCurrentLoc] = useState(() => {
    try {
      const saved = localStorage.getItem('smartcart_location')
      return saved ? JSON.parse(saved) : { area: 'Indiranagar', city: 'Bengaluru', pincode: '560038' }
    } catch {
      return { area: 'Indiranagar', city: 'Bengaluru', pincode: '560038' }
    }
  })

  const cartCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0
  const cartTotal = cart?.items?.reduce((sum, item) => sum + (item.product?.price || 0) * item.quantity, 0) || 0

  const handleNavSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (navSearch.trim()) {
      navigate(`/collections?search=${encodeURIComponent(navSearch.trim())}`)
    }
  }

  const handleSelectLocation = (loc: { area: string; city: string; pincode: string }) => {
    setCurrentLoc(loc)
    try {
      localStorage.setItem('smartcart_location', JSON.stringify(loc))
    } catch {}
    setShowLocationModal(false)
    toast({
      title: 'Location Updated',
      description: `Delivering to ${loc.area}, ${loc.city} (${loc.pincode})`,
    })
  }

  const handleDetectGps = () => {
    setDetectingGps(true)
    if (!navigator.geolocation) {
      toast({ title: 'GPS Unavailable', description: 'Geolocation is not supported by your browser.', variant: 'destructive' })
      setDetectingGps(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      () => {
        // Detected area
        const gpsLoc = { area: 'Indiranagar Central', city: 'Bengaluru', pincode: '560038' }
        handleSelectLocation(gpsLoc)
        setDetectingGps(false)
      },
      () => {
        toast({ title: 'GPS Permission Denied', description: 'Using default area Indiranagar, Bengaluru.', variant: 'destructive' })
        setDetectingGps(false)
      },
      { timeout: 5000 }
    )
  }

  const filteredLocations = POPULAR_LOCATIONS.filter((l) =>
    l.area.toLowerCase().includes(locSearch.toLowerCase()) ||
    l.city.toLowerCase().includes(locSearch.toLowerCase()) ||
    l.pincode.includes(locSearch)
  )

  return (
    <div className="sticky top-0 z-40 w-full shadow-xs">
      {/* Top Banner */}
      <div className="bg-primary text-primary-foreground text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2">
        <span className="inline-flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-full text-[11px] font-bold">
          ⚡ 10 MINS
        </span>
        <span>Express Delivery in {currentLoc.city} • Free Shipping over ₹299!</span>
      </div>

      <header className="border-b border-border bg-background/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          {/* Logo & Interactive Location */}
          <div className="flex items-center gap-4 shrink-0">
            <Link to="/" aria-label="SmartCart home">
              <Logo />
            </Link>

            {/* Delivery Location badge */}
            <button
              onClick={() => setShowLocationModal(true)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/60 hover:bg-muted px-3 py-1.5 rounded-full border border-border/80 transition cursor-pointer"
            >
              <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
              <span className="font-semibold text-foreground truncate max-w-[120px]">{currentLoc.area}</span>
              <span className="text-[10px] text-muted-foreground font-mono">{currentLoc.pincode}</span>
            </button>
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

      {/* Interactive Location Selection Modal */}
      {showLocationModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border max-w-md w-full rounded-3xl p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-extrabold text-foreground flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-primary" /> Select Delivery Location
                </h3>
                <p className="text-xs text-muted-foreground">Select your area for 10-minute grocery delivery</p>
              </div>
              <button
                onClick={() => setShowLocationModal(false)}
                className="h-8 w-8 rounded-full hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* GPS Auto Detect */}
            <button
              onClick={handleDetectGps}
              disabled={detectingGps}
              className="w-full flex items-center justify-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-2xl py-3 text-xs font-bold transition cursor-pointer"
            >
              {detectingGps ? <Loader2 className="h-4 w-4 animate-spin" /> : <Navigation className="h-4 w-4" />}
              {detectingGps ? 'Detecting Location...' : 'Use Current GPS Location'}
            </button>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={locSearch}
                onChange={(e) => setLocSearch(e.target.value)}
                placeholder="Search city, area or pincode..."
                className="w-full h-10 pl-9 pr-4 text-xs bg-muted/50 border border-border rounded-xl text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition"
              />
            </div>

            {/* Popular Locations List */}
            <div>
              <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Popular Delivery Hubs</p>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {filteredLocations.map((loc) => {
                  const isSelected = currentLoc.area === loc.area && currentLoc.pincode === loc.pincode
                  return (
                    <button
                      key={loc.area}
                      onClick={() => handleSelectLocation(loc)}
                      className={cn(
                        'w-full flex items-center justify-between p-3 rounded-xl border text-left text-xs transition cursor-pointer',
                        isSelected
                          ? 'bg-primary/10 border-primary text-primary font-bold'
                          : 'border-border hover:bg-muted text-foreground'
                      )}
                    >
                      <div>
                        <p className="font-semibold text-foreground">{loc.area}, {loc.city}</p>
                        <p className="text-[10px] text-muted-foreground">Pincode: {loc.pincode}</p>
                      </div>
                      {isSelected && <Check className="h-4 w-4 text-primary shrink-0" />}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}