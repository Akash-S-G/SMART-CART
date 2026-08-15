import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ScanLine,
  Zap,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Star,
  Plus,
  Minus,
  Search,
  ShoppingCart,
  Clock,
  CheckCircle2,
  Camera,
  Flame,
  Award,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listProductsApi } from '@/lib/api'
import { useCart } from '@/hooks/use-cart'
import { useToast } from '@/components/ui/use-toast'
import { useState } from 'react'

const CATEGORY_TAGS = [
  { name: 'Dairy & Eggs', icon: '🥛', category: 'Dairy' },
  { name: 'Atta & Rice', icon: '🌾', category: 'Staples' },
  { name: 'Snacks & Chips', icon: '🍿', category: 'Snacks' },
  { name: 'Fresh Vegetables', icon: '🥬', category: 'Produce' },
  { name: 'Cold Drinks', icon: '🥤', category: 'Beverages' },
  { name: 'Bakery & Bread', icon: '🍞', category: 'Bakery' },
  { name: 'Personal Care', icon: '🧼', category: 'Personal Care' },
]

export function LandingPage() {
  const navigate = useNavigate()
  const { cart, addItem, updateQuantity } = useCart()
  const { toast } = useToast()
  const [searchVal, setSearchVal] = useState('')

  const { data: featuredProducts, isLoading } = useQuery({
    queryKey: ['featured-products'],
    queryFn: () => listProductsApi(0, 8),
  })

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchVal.trim()) {
      navigate(`/collections?search=${encodeURIComponent(searchVal.trim())}`)
    }
  }

  const getItemQuantity = (productId: string) => {
    const found = cart?.items?.find((item) => item.product_id === productId)
    return found ? found.quantity : 0
  }

  const handleAddOrIncrement = async (e: React.MouseEvent, productId: string, name: string) => {
    e.preventDefault()
    e.stopPropagation()
    const currentQty = getItemQuantity(productId)
    try {
      if (currentQty === 0) {
        await addItem(productId, 1)
        toast({ title: 'Added to Cart', description: `${name} added to your cart.` })
      } else {
        await updateQuantity(productId, currentQty + 1)
      }
    } catch {
      toast({
        title: 'Sign In Required',
        description: 'Please sign in to manage your shopping cart.',
        variant: 'destructive',
      })
    }
  }

  const handleDecrement = async (e: React.MouseEvent, productId: string) => {
    e.preventDefault()
    e.stopPropagation()
    const currentQty = getItemQuantity(productId)
    if (currentQty <= 1) {
      await updateQuantity(productId, 0)
    } else {
      await updateQuantity(productId, currentQty - 1)
    }
  }

  return (
    <div className="flex flex-col w-full bg-background text-foreground">
      {/* Hero Section */}
      <section className="relative w-full pt-12 pb-16 px-4 sm:px-6 lg:px-8 border-b border-border bg-gradient-to-b from-muted/40 via-background to-background">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero Content */}
          <div className="lg:col-span-7 flex flex-col gap-6 text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-semibold w-fit">
              <Zap className="h-3.5 w-3.5 text-primary shrink-0" />
              <span>10-Minute Express Grocery Delivery</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.1] text-foreground">
              Fresh Groceries & Instant <br className="hidden sm:inline" />
              <span className="text-primary">AI Vision Checkout</span>
            </h1>

            <p className="text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed">
              Scan items directly using your smartphone camera or shop 700+ authentic Indian groceries delivered fresh to your doorstep in minutes.
            </p>

            {/* Quick Search Bar */}
            <form onSubmit={handleSearchSubmit} className="w-full max-w-xl relative flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                value={searchVal}
                onChange={(e) => setSearchVal(e.target.value)}
                placeholder="Search products, brands, or categories (e.g., Amul, Atta, Milk)..."
                className="w-full h-13 pl-12 pr-28 text-sm bg-card border border-border rounded-2xl shadow-xs text-foreground placeholder:text-muted-foreground/70 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
              />
              <Button
                type="submit"
                size="sm"
                className="absolute right-2 h-9 px-4 rounded-xl bg-primary text-primary-foreground font-semibold text-xs shadow-xs hover:opacity-90"
              >
                Search
              </Button>
            </form>

            {/* Quick Category Chips */}
            <div className="flex items-center gap-2 flex-wrap pt-2">
              <span className="text-xs font-semibold text-muted-foreground mr-1">Popular:</span>
              {CATEGORY_TAGS.map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => navigate(`/collections?category=${cat.category}`)}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-card border border-border text-xs font-semibold text-foreground hover:border-primary/50 hover:bg-muted/50 transition-all"
                >
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Right Hero Card: Camera Scanner Live Highlight */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="w-full max-w-md bg-card border border-border rounded-3xl p-6 shadow-xl relative overflow-hidden">
              <div className="flex items-center justify-between border-b border-border pb-4 mb-5">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Camera className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">AI Camera Scanner</h3>
                    <p className="text-[11px] text-muted-foreground">Instant Item Detection</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-[10px] border-primary/30 text-primary bg-primary/5 font-semibold">
                  LIVE VISION
                </Badge>
              </div>

              {/* Viewfinder Mockup */}
              <div className="relative aspect-video w-full rounded-2xl bg-zinc-900 overflow-hidden flex items-center justify-center border border-zinc-800 shadow-inner group">
                <img
                  src="https://images.unsplash.com/photo-1550989460-0adf9ea622e2?auto=format&fit=crop&w=800&q=80"
                  alt="Grocery scanner preview"
                  className="w-full h-full object-cover opacity-80"
                />

                {/* Corner Targeting Overlay */}
                <div className="absolute inset-4 border-2 border-dashed border-emerald-400/70 rounded-xl pointer-events-none flex flex-col justify-between p-2">
                  <div className="flex justify-between">
                    <span className="h-3 w-3 border-t-2 border-l-2 border-emerald-400"></span>
                    <span className="h-3 w-3 border-t-2 border-r-2 border-emerald-400"></span>
                  </div>
                  <div className="flex justify-between">
                    <span className="h-3 w-3 border-b-2 border-l-2 border-emerald-400"></span>
                    <span className="h-3 w-3 border-b-2 border-r-2 border-emerald-400"></span>
                  </div>
                </div>

                {/* Bounding box mock label */}
                <div className="absolute bottom-3 left-3 bg-zinc-900/90 text-white border border-emerald-500/40 text-[11px] font-semibold px-2.5 py-1 rounded-lg flex items-center gap-1.5 backdrop-blur-xs">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
                  <span>Detected: Fresh Farm Tomatoes & Capsicum • 99.4%</span>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between pt-2">
                <div className="text-xs">
                  <span className="font-semibold text-foreground">Point & Scan Instant Cart</span>
                  <p className="text-[11px] text-muted-foreground">No barcodes needed — powered by YOLO11</p>
                </div>
                <Button
                  size="sm"
                  onClick={() => navigate('/scanner')}
                  className="h-9 px-4 rounded-xl bg-primary text-primary-foreground font-semibold text-xs gap-1.5 shadow-xs"
                >
                  <ScanLine className="h-4 w-4" /> Start Scan
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Value Props Bar */}
      <section className="w-full py-8 border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-foreground">10 Min Delivery</h4>
              <p className="text-[11px] text-muted-foreground">Lightning fast order dispatch</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-foreground">700+ Authentic Products</h4>
              <p className="text-[11px] text-muted-foreground">Indian grocery staples</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0">
              <Camera className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-foreground">AI Camera Scan</h4>
              <p className="text-[11px] text-muted-foreground">Visual recognition checkout</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-foreground">100% Quality Assurance</h4>
              <p className="text-[11px] text-muted-foreground">Freshness & purity verified</p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products Section */}
      <section className="w-full py-16 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-7xl mx-auto flex flex-col gap-8">
          <div className="flex items-end justify-between border-b border-border pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-primary uppercase tracking-wider mb-1">
                <Flame className="h-4 w-4" /> Trending Groceries
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">Popular Daily Essentials</h2>
            </div>
            <Link
              to="/collections"
              className="text-xs font-bold text-primary hover:underline inline-flex items-center gap-1"
            >
              Explore Full Catalog <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Product Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-72 rounded-2xl bg-card border border-border animate-pulse"></div>
                ))
              : featuredProducts?.map((p) => {
                  const qty = getItemQuantity(p.id)
                  const originalPrice = Math.round(p.price * 1.15)
                  return (
                    <div
                      key={p.id}
                      onClick={() => navigate(`/product/${p.id}`)}
                      className="group bg-card border border-border rounded-2xl p-3 sm:p-4 flex flex-col justify-between hover:border-primary/50 hover:shadow-md transition-all cursor-pointer relative"
                    >
                      {/* Product Image */}
                      <div className="relative w-full aspect-square rounded-xl bg-muted/30 overflow-hidden flex items-center justify-center p-2 mb-3">
                        <img
                          src={p.images?.[0] || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=500&q=80'}
                          alt={p.name}
                          className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
                        />
                        <span className="absolute top-2 left-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-extrabold text-[10px] px-2 py-0.5 rounded-md border border-emerald-500/20">
                          15% OFF
                        </span>
                      </div>

                      {/* Product Info */}
                      <div className="flex flex-col gap-1 flex-1 justify-between">
                        <div>
                          <p className="text-[11px] text-muted-foreground font-medium truncate">{p.category || 'Grocery'}</p>
                          <h3 className="text-xs sm:text-sm font-bold text-foreground line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                            {p.name}
                          </h3>
                        </div>

                        <div className="mt-3 flex items-center justify-between pt-2 border-t border-border/60">
                          <div>
                            <div className="flex items-baseline gap-1.5">
                              <span className="text-sm sm:text-base font-extrabold text-foreground">₹{p.price}</span>
                              <span className="text-[11px] text-muted-foreground line-through">₹{originalPrice}</span>
                            </div>
                          </div>

                          {/* Add / Quantity Control Button */}
                          {qty === 0 ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => handleAddOrIncrement(e, p.id, p.name)}
                              className="h-8 px-3 rounded-xl border-primary/40 text-primary hover:bg-primary hover:text-white font-bold text-xs gap-1"
                            >
                              <Plus className="h-3.5 w-3.5" /> ADD
                            </Button>
                          ) : (
                            <div className="flex items-center bg-primary text-primary-foreground rounded-xl h-8 px-1">
                              <button
                                onClick={(e) => handleDecrement(e, p.id)}
                                className="h-7 w-7 flex items-center justify-center hover:bg-white/20 rounded-lg text-white font-bold"
                              >
                                <Minus className="h-3.5 w-3.5" />
                              </button>
                              <span className="px-2 font-extrabold text-xs text-white">{qty}</span>
                              <button
                                onClick={(e) => handleAddOrIncrement(e, p.id, p.name)}
                                className="h-7 w-7 flex items-center justify-center hover:bg-white/20 rounded-lg text-white font-bold"
                              >
                                <Plus className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
          </div>
        </div>
      </section>

      {/* How AI Vision Works Section */}
      <section className="w-full py-16 px-4 sm:px-6 lg:px-8 bg-muted/30 border-t border-border">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <Badge variant="outline" className="mb-2 border-primary/30 text-primary bg-primary/5 font-semibold text-xs">
              SIMPLE & FAST
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">How SmartCart AI Works</h2>
            <p className="text-sm text-muted-foreground mt-2">Skip tedious searching. Identify and buy groceries instantly with your camera.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4 text-left shadow-xs">
              <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary font-black text-lg flex items-center justify-center">
                1
              </div>
              <h3 className="text-base font-bold text-foreground">Point Your Camera</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Open the AI Scanner on any smartphone or tablet and point the camera at any grocery product package or fresh item.
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4 text-left shadow-xs">
              <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary font-black text-lg flex items-center justify-center">
                2
              </div>
              <h3 className="text-base font-bold text-foreground">Instant Recognition</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Our custom YOLO11 model detects the item, extracts OCR text, matches price, stock, and item details in milliseconds.
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4 text-left shadow-xs">
              <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary font-black text-lg flex items-center justify-center">
                3
              </div>
              <h3 className="text-base font-bold text-foreground">1-Tap Cart & Express Checkout</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Review your auto-populated cart, apply instant discount coupons, and complete checkout with UPI or Cash on Delivery.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}