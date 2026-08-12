import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ScanLine,
  Zap,
  QrCode,
  Building2,
  ArrowRight,
  Sparkles,
  Code2,
  Star,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  ShoppingCart,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listProductsApi } from '@/lib/api'
import { useCart } from '@/hooks/use-cart'
import { useToast } from '@/components/ui/use-toast'
import { useState } from 'react'

const BRANDS = ['NEXUS', 'AURALIGHT', 'QUANTUM', 'VELOCITY']

export function LandingPage() {
  const navigate = useNavigate()
  const { addItem } = useCart()
  const { toast } = useToast()
  const [searchVal, setSearchVal] = useState('')

  const { data: featuredProducts, isLoading } = useQuery({
    queryKey: ['featured-products'],
    queryFn: () => listProductsApi(0, 4),
  })

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchVal.trim()) {
      navigate(`/collections?search=${encodeURIComponent(searchVal.trim())}`)
    }
  }

  const handleQuickAdd = async (e: React.MouseEvent, productId: string, name: string) => {
    e.preventDefault()
    try {
      await addItem(productId, 1)
      toast({
        title: 'Added to Cart',
        description: `${name} has been added to your shopping cart.`,
      })
    } catch (err: any) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to add items to your cart.',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="flex flex-col w-full text-on-surface bg-background">
      {/* Hero Section */}
      <section className="w-full min-h-[70vh] flex flex-col items-center justify-center pt-24 pb-16 px-6 relative overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[120px] -z-10 mix-blend-multiply"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/10 rounded-full blur-[100px] -z-10 mix-blend-multiply"></div>

        <div className="text-center max-w-3xl mx-auto flex flex-col items-center gap-6 relative z-10">
          <Badge variant="ai" className="relative gap-1.5 px-3.5 py-1">
            <ScanLine className="h-3.5 w-3.5 text-secondary" /> Powered by Neural Search
          </Badge>

          <h1 className="font-sans font-extrabold text-5xl md:text-7xl leading-[1.05] tracking-tighter text-foreground">
            Shop Smarter with <br />
            <span className="text-gradient inline-block animate-pulse">AI Vision</span>
          </h1>

          <p className="font-sans text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            Experience seamless retail. Point your camera, instantly recognize products, compare real-time prices, and checkout without friction.
          </p>

          <form onSubmit={handleSearchSubmit} className="w-full max-w-2xl mt-8 relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-muted-foreground" />
            </div>
            <input
              type="text"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              className="w-full bg-card border border-black/10 text-foreground rounded-full py-5 pl-12 pr-16 shadow-lg outline-none transition-all duration-300 focus:border-primary/40 focus:shadow-xl focus:shadow-primary/5 placeholder:text-muted-foreground/60 text-lg"
              placeholder="Search or scan any product..."
            />
            <div className="absolute inset-y-2 right-2 flex items-center">
              <button
                type="button"
                onClick={() => navigate('/scanner')}
                aria-label="Start AI Scan"
                className="bg-primary text-primary-foreground w-12 h-12 rounded-full flex items-center justify-center transition-transform hover:scale-105 shadow-md shadow-primary/20"
              >
                <ScanLine className="h-5 w-5" />
              </button>
            </div>
          </form>

          <div className="flex items-center gap-3 mt-6 text-xs text-muted-foreground uppercase tracking-widest">
            <span className="w-8 h-[1px] bg-border"></span>
            <span>Real-time Retail Processing</span>
            <span className="w-8 h-[1px] bg-border"></span>
          </div>
        </div>
      </section>

      {/* Grid Features */}
      <section className="w-full max-w-7xl mx-auto px-6 pb-20 relative z-20 -mt-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-1 md:col-span-2 bg-card rounded-3xl p-8 border border-border flex flex-col justify-between overflow-hidden relative group hover:border-primary/30 transition-all duration-300">
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-secondary/10 text-secondary rounded-full text-xs font-semibold mb-4">
                <Zap className="h-3.5 w-3.5" /> Real-time Processing
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-2">Instant Recognition</h3>
              <p className="text-muted-foreground text-sm max-w-sm">Identify thousands of products in milliseconds using our edge-optimized AI models.</p>
            </div>
            <div className="mt-8 flex items-baseline gap-2">
              <span className="text-6xl font-extrabold text-foreground tracking-tighter leading-none">99.8</span>
              <span className="text-lg text-muted-foreground">% Accuracy</span>
            </div>
            <div className="absolute right-0 bottom-0 w-64 h-64 bg-secondary/5 rounded-full blur-3xl translate-x-1/4 translate-y-1/4 transition-transform duration-700 group-hover:scale-110"></div>
          </div>

          <div className="col-span-1 bg-primary text-primary-foreground rounded-3xl p-8 flex flex-col justify-between relative overflow-hidden group">
            <div className="relative z-10">
              <h3 className="text-2xl font-bold mb-2">Active Users</h3>
              <p className="text-primary-foreground/75 text-sm">Global adoption scaling rapidly across major retail hubs.</p>
            </div>
            <div className="mt-8">
              <div className="text-5xl font-extrabold tracking-tighter leading-none">2.4M</div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          </div>

          <div className="col-span-1 bg-card border border-border rounded-3xl p-8 flex flex-col justify-between hover:border-primary/30 transition-all duration-300">
            <div>
              <div className="w-12 h-12 bg-black/[0.04] flex items-center justify-center rounded-xl mb-6 text-foreground">
                <QrCode className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2">Zero Friction</h3>
            </div>
            <p className="text-muted-foreground text-sm mt-4">Eliminate checkout lines. Scan, pay, and walk out.</p>
          </div>

          <div className="col-span-1 md:col-span-2 bg-card border border-border rounded-3xl p-8 flex items-center justify-between relative overflow-hidden group hover:border-primary/30 transition-all duration-300">
            <div className="relative z-10 max-w-md">
              <h3 className="text-xl font-bold text-foreground mb-3">Enterprise Ready</h3>
              <p className="text-muted-foreground text-sm mb-6">Integrate SmartCart vision APIs directly into your existing retail infrastructure.</p>
              <a onClick={() => navigate('/analytics')} className="inline-flex items-center gap-2 text-sm text-primary font-bold hover:text-secondary transition-colors cursor-pointer uppercase tracking-wider">
                View Intelligence Dashboard <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </a>
            </div>
            <div className="hidden md:block w-32 h-32 relative shrink-0">
              <div className="absolute inset-0 border border-primary/20 rounded-full animate-ping"></div>
              <div className="absolute inset-4 border border-primary/40 rounded-full flex items-center justify-center bg-card shadow-sm z-10">
                <Building2 className="h-8 w-8 text-primary" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trusted Brands */}
      <section className="w-full py-12 border-y border-border bg-card/50 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Trusted by Global Retailers</p>
        </div>
        <div className="flex justify-center items-center gap-12 flex-wrap">
          {BRANDS.map((b) => (
            <span key={b} className="font-mono text-xl font-extrabold tracking-[0.2em] text-muted-foreground/40">{b}</span>
          ))}
        </div>
      </section>

      {/* Featured Products */}
      <section className="w-full py-20 border-b border-border bg-card/20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center mb-12">
            <div>
              <h2 className="text-3xl font-bold text-foreground tracking-tight">Featured Products</h2>
              <p className="text-muted-foreground text-sm mt-1">Curated picks from our neural catalog</p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" size="icon" aria-label="Previous">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="secondary" size="icon" aria-label="Next">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse bg-card rounded-3xl p-4 border border-border h-80"></div>
              ))
            ) : (
              featuredProducts?.map((p, i) => (
                <Link
                  to={`/product/${p.id}`}
                  key={p.id}
                  className="group flex flex-col justify-between cursor-pointer bg-card p-4 rounded-3xl border border-border hover:border-primary/40 hover:shadow-xl transition-all duration-300"
                >
                  <div className="relative w-full aspect-[4/5] bg-card overflow-hidden rounded-2xl border border-black/5 shrink-0">
                    <img
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                      src={p.images?.[0] || 'https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80'}
                      alt={p.name}
                    />
                  </div>

                  <div className="flex flex-col gap-2 pt-3 px-1 flex-1 justify-between">
                    <div className="flex items-center justify-between gap-2 min-h-[22px]">
                      {i === 0 ? (
                        <Badge variant="ai" className="gap-1 text-[10px] font-semibold py-0.5 px-2">
                          <Sparkles className="h-3 w-3 text-secondary" /> Best Seller
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px] font-semibold py-0.5 px-2">
                          Featured
                        </Badge>
                      )}
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-foreground truncate group-hover:text-primary transition-colors">{p.name}</h3>
                      <p className="text-xs text-muted-foreground truncate">{p.brand || 'SmartCart Essentials'}</p>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-border/60 mt-1">
                      <span className="text-lg font-extrabold text-foreground">₹{p.price}</span>
                      <Button
                        size="sm"
                        variant="gradient"
                        onClick={(e) => handleQuickAdd(e, p.id, p.name)}
                        className="rounded-xl text-xs font-bold uppercase tracking-wider h-8 px-3 gap-1 shadow-xs"
                      >
                        <ShoppingCart className="h-3.5 w-3.5" /> Add
                      </Button>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  )
}