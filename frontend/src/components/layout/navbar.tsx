import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Sun, Moon, Package, Camera, MapPin, Search, Navigation, Check, X, Loader2, Menu } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { useTheme } from '@/hooks/use-theme'
import { useLanguage } from '@/hooks/use-language'
import { useState, useEffect, useRef } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { getAutocompleteApi } from '@/lib/api'
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
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const navSearchRef = useRef<HTMLInputElement>(null)
  const [showLocationModal, setShowLocationModal] = useState(false)
  const [locSearch, setLocSearch] = useState('')
  const [detectingGps, setDetectingGps] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

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
      setShowSuggestions(false)
      navigate(`/collections?search=${encodeURIComponent(navSearch.trim())}`)
    }
  }

  // Autocomplete with debounce
  useEffect(() => {
    if (navSearch.trim().length < 2) {
      setSuggestions([])
      return
    }
    const id = setTimeout(async () => {
      try {
        const res = await getAutocompleteApi(navSearch.trim())
        setSuggestions(res)
        setShowSuggestions(true)
      } catch {
        setSuggestions([])
      }
    }, 250)
    return () => clearTimeout(id)
  }, [navSearch])

  // close suggestions on outside click
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (navSearchRef.current && !navSearchRef.current.contains(e.target as Node)) {
        // check if click is on suggestions box
        const sug = document.getElementById('nav-autocomplete')
        if (sug && sug.contains(e.target as Node)) return
        setShowSuggestions(false)
      }
    }
    window.addEventListener('mousedown', onClick)
    return () => window.removeEventListener('mousedown', onClick)
  }, [])

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
      async (position) => {
        const { latitude, longitude } = position.coords
        try {
          // Live reverse geocoding via OpenStreetMap Nominatim API
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`
          )
          const data = await res.json()
          const addr = data.address || {}

          const area =
            addr.suburb ||
            addr.neighbourhood ||
            addr.residential ||
            addr.subdistrict ||
            addr.quarter ||
            addr.town ||
            addr.city_district ||
            addr.city ||
            'Detected Location'

          const city = addr.city || addr.town || addr.state_district || addr.state || 'Bengaluru'
          const pincode = addr.postcode || '560038'

          const detectedLoc = { area, city, pincode }
          handleSelectLocation(detectedLoc)
          toast({
            title: 'GPS Location Updated',
            description: `Detected: ${area}, ${city} (${pincode})`,
          })
        } catch {
          const fallbackLoc = { area: `Lat ${latitude.toFixed(2)}, Lon ${longitude.toFixed(2)}`, city: 'Bengaluru', pincode: '560038' }
          handleSelectLocation(fallbackLoc)
        } finally {
          setDetectingGps(false)
        }
      },
      (error) => {
        let msg = 'Unable to fetch GPS coordinates.'
        if (error.code === error.PERMISSION_DENIED) msg = 'GPS permission denied. Please allow location access in browser.'
        else if (error.code === error.POSITION_UNAVAILABLE) msg = 'Location signal unavailable.'
        else if (error.code === error.TIMEOUT) msg = 'GPS request timed out.'

        toast({ title: 'GPS Error', description: msg, variant: 'destructive' })
        setDetectingGps(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  const filteredLocations = POPULAR_LOCATIONS.filter((l) =>
    l.area.toLowerCase().includes(locSearch.toLowerCase()) ||
    l.city.toLowerCase().includes(locSearch.toLowerCase()) ||
    l.pincode.includes(locSearch)
  )

  // body scroll lock + Esc for modal
  useEffect(() => {
    if (!showLocationModal) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setShowLocationModal(false) }
    window.addEventListener('keydown', onEsc)
    return () => { document.body.style.overflow = prev; window.removeEventListener('keydown', onEsc) }
  }, [showLocationModal])

  // close mobile drawer on route change
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  return (
    <div className="sticky top-0 z-40 w-full">
      {/* Top Banner */}
      <div className="bg-primary text-primary-foreground text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2">
        <span className="inline-flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-full text-[11px] font-bold ring-1 ring-white/20">
          ⚡ 10 MINS
        </span>
        <span>Express Delivery in {currentLoc.city} • Free Shipping over ₹299!</span>
      </div>

      <header className="border-b border-border bg-background/85 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70 shadow-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 sm:gap-4 px-4 sm:px-6 lg:px-8">
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
          <form onSubmit={handleNavSearch} className="hidden md:flex flex-1 max-w-md mx-4 relative" ref={navSearchRef as any}>
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={navSearch}
              onChange={(e) => setNavSearch(e.target.value)}
              onFocus={() => navSearch.trim().length >= 2 && setShowSuggestions(true)}
              placeholder="Search groceries (e.g. Milk, Atta, Eggs)..."
              className="w-full h-9 pl-9 pr-4 text-xs bg-muted/50 border border-border rounded-full text-foreground placeholder:text-muted-foreground/70 outline-none focus:border-primary focus:bg-background transition-all"
              autoComplete="off"
            />
            {showSuggestions && suggestions.length > 0 && (
              <div id="nav-autocomplete" className="absolute top-full mt-2 left-0 right-0 bg-card border border-border rounded-2xl shadow-xl overflow-hidden z-50">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => {
                      setNavSearch(s)
                      setShowSuggestions(false)
                      navigate(`/collections?search=${encodeURIComponent(s)}`)
                    }}
                    className="w-full text-left px-4 py-2.5 text-xs font-medium text-foreground hover:bg-muted flex items-center gap-2"
                  >
                    <Search className="h-3.5 w-3.5 text-muted-foreground" /> {s}
                  </button>
                ))}
              </div>
            )}
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

          {/* Mobile hamburger */}
          <button
            aria-label="Open menu"
            className="xl:hidden h-9 w-9 inline-flex items-center justify-center rounded-xl border border-border hover:bg-muted text-muted-foreground"
            onClick={() => setMobileOpen(v => !v)}
          >
            <Menu className="h-4 w-4" />
          </button>

          {/* Action Buttons */}
          <div className="flex items-center gap-1 sm:gap-2">
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

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="xl:hidden border-b border-border bg-card">
          <div className="mx-auto max-w-7xl px-4 py-3 flex flex-col gap-2">
            <form onSubmit={handleNavSearch} className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                value={navSearch} onChange={e => setNavSearch(e.target.value)}
                placeholder="Search groceries…"
                className="w-full h-10 pl-9 pr-4 text-sm bg-muted/50 border border-border rounded-xl text-foreground placeholder:text-muted-foreground/70 outline-none focus:border-primary"
                autoComplete="off"
              />
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-card border border-border rounded-xl shadow-lg z-50 overflow-hidden">
                  {suggestions.map((s) => (
                    <button key={s} type="button" onClick={() => { setNavSearch(s); setShowSuggestions(false); navigate(`/collections?search=${encodeURIComponent(s)}`); }} className="w-full text-left px-3 py-2 text-xs font-medium hover:bg-muted flex items-center gap-2">
                      <Search className="h-3 w-3.5 text-muted-foreground" /> {s}
                    </button>
                  ))}
                </div>
              )}
            </form>
            <nav className="flex flex-wrap gap-1.5 pt-1">
              {NAV_LINKS.map(link => (
                <NavLink key={link.to} to={link.to} className={({isActive})=> cn('rounded-full px-3 py-1.5 text-xs font-bold border', isActive ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted text-foreground border-border') }>
                  {link.label}
                </NavLink>
              ))}
              {user?.role==='admin' && (<NavLink to="/admin" className={({isActive})=> cn('rounded-full px-3 py-1.5 text-xs font-bold border', isActive ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted text-foreground border-border')}>Admin</NavLink>)}
            </nav>
          </div>
        </div>
      )}

      {/* Interactive Location Selection Modal */}
      {showLocationModal && (
        <div
          role="dialog" aria-modal="true" aria-label="Select delivery location"
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowLocationModal(false)}
        >
          <div
            className="bg-card border border-border max-w-md w-full rounded-3xl p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in duration-200"
            onClick={e => e.stopPropagation()}
          >
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