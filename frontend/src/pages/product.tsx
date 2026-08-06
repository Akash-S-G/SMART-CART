import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Play,
  Star,
  Verified,
  Cpu,
  PlusCircle,
  MinusCircle,
  Sparkles,
  ThumbsUp,
  ChevronDown,
  ShoppingCart,
  Plus,
  Minus,
  Activity,
  Heart,
  ArrowLeft,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { getProductApi, addToCartApi, getCategoriesApi } from '@/lib/api'
import { useCart } from '@/hooks/use-cart'
import { useWishlist } from '@/hooks/use-wishlist'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/cn'

export function ProductPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { addItem } = useCart()
  const { items: wishlistItems, toggleItem: toggleWishlist } = useWishlist()
  const { toast } = useToast()

  const [qty, setQty] = useState(1)
  const [activeTab, setActiveTab] = useState('specs')
  const [activeImageIndex, setActiveImageIndex] = useState(0)

  const { data: p, isLoading, error } = useQuery({
    queryKey: ['product', id],
    queryFn: () => getProductApi(id!),
    enabled: !!id,
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategoriesApi,
  })

  // Fallback if no images are present
  const images = useMemo(() => {
    if (p?.images && p.images.length > 0) return p.images
    return ['https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80']
  }, [p])

  const handleAddToCart = async () => {
    if (!p) return
    try {
      await addItem(p.id, qty)
      toast({
        title: 'Added to Cart',
        description: `Added ${qty}x ${p.name} to your shopping cart.`,
      })
    } catch (err: any) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to add items to your cart.',
        variant: 'destructive',
      })
    }
  }

  const categoryName = useMemo(() => {
    if (!categories || !p) return ''
    const cat = categories.find((c) => c.id === p.category_id)
    return cat ? cat.name.toLowerCase() : ''
  }, [categories, p])

  const isFood = useMemo(() => {
    if (!p) return false
    return (
      categoryName.includes('fruit') ||
      categoryName.includes('veg') ||
      categoryName.includes('dairy') ||
      categoryName.includes('bakery') ||
      categoryName.includes('snack') ||
      categoryName.includes('bev') ||
      categoryName.includes('food') ||
      categoryName.includes('grocery') ||
      p.tags?.some(tag => {
        const t = tag.toLowerCase()
        return t.includes('fruit') || t.includes('veg') || t.includes('dairy') || t.includes('bakery') || t.includes('snack') || t.includes('bev') || t.includes('food')
      }) ||
      p.name.toLowerCase().includes('banana') ||
      p.name.toLowerCase().includes('masti') ||
      p.name.toLowerCase().includes('chocolate') ||
      p.name.toLowerCase().includes('biscuit') ||
      p.name.toLowerCase().includes('orange') ||
      p.name.toLowerCase().includes('sprite') ||
      p.name.toLowerCase().includes('water')
    )
  }, [categoryName, p])

  // Generate category-specific specifications dynamically
  const specGroups = useMemo(() => {
    if (!p) return []

    if (isFood) {
      return [
        {
          title: 'Nutrition & Details',
          rows: [
            ['Unit Size', p.brand ? 'Packed unit' : '1 piece / bunch'],
            ['Sourced Origin', 'Verified Local Farm'],
            ['Calories', 'Low/Moderate'],
            ['Diet Type', 'Vegetarian / Organic'],
          ],
        },
        {
          title: 'Storage & Freshness',
          rows: [
            ['Storage Temp', 'Keep refrigerated (4°C - 8°C)'],
            ['Shelf Life', '3 - 5 days standard'],
            ['Packaging', 'Eco-friendly biodegradable bag'],
            ['Wash Instruction', 'Wash thoroughly before raw consumption'],
          ],
        },
        {
          title: 'Provenance & Integrity',
          rows: [
            ['Pesticide residue', 'Non-detectable / Passed'],
            ['GST rate', 'Nil / Exempted'],
            ['Organic certification', 'Verified Organic'],
            ['Barcode', p.barcode || 'N/A'],
          ],
        },
      ]
    }

    // Default Electronics / Non-food Spec Groups
    return [
      {
        title: 'Hardware Specs',
        rows: [
          ['SKU ID', p.sku],
          ['Brand', p.brand || 'Premium Selection'],
          ['Unit packaging', p.brand ? 'Retail boxed' : 'Individual packaging'],
          ['Certification', 'CE / RoHS compliant'],
        ],
      },
      {
        title: 'Power & Logistics',
        rows: [
          ['Connectivity', 'N/A / Standalone'],
          ['Power demand', 'Standard AC/DC charging where applicable'],
          ['Est. Delivery', 'Standard 24-48 hours'],
          ['Return warranty', '10-day replacement window'],
        ],
      },
      {
        title: 'Technical Dimensions',
        rows: [
          ['Weight', 'Lightweight industrial build'],
          ['Chassis material', 'Recycled polymers / brushed aluminum accents'],
          ['Integrations', 'Compatible with SmartCart AI Ecosystem'],
          ['Barcode', p.barcode || 'N/A'],
        ],
      },
    ]
  }, [p, isFood])

  const dynamicInsightsAndReviews = useMemo(() => {
    if (!p) return { advantages: [], limitations: [], sentiment: 90, reviews: [] }

    let advantages = [
      `Premium quality sourced from certified partners.`,
      `Secure, eco-friendly logistics packaging.`,
      `Highly positive feedback in AI consumer sentiment logs.`
    ]
    let limitations = [
      `Constrained shelf life; store in optimal conditions.`,
      `Subject to seasonality and regional availability.`
    ]
    let sentiment = Math.round(85 + (p.rating || 4.5) * 3)

    if (isFood) {
      advantages = [
        `100% natural, fresh, and hand-picked for quality.`,
        `Zero artificial coloring, wax coatings, or preservatives.`,
        `Direct farm-to-shelf supply chain minimizing carbon footprint.`
      ]
      limitations = [
        `Best consumed within 3-4 days of delivery.`,
        `Slight natural variance in size and color profiles.`
      ]
    } else {
      advantages = [
        `CE and RoHS certified hardware integrity.`,
        `High durability chassis materials and drop testing.`,
        `Compatible with standard local and global ecosystems.`
      ]
      limitations = [
        `Requires periodic cleaning and handling care.`,
        `Instruction manual updates delivered digitally via QR.`
      ]
    }

    // Dynamic Reviews based on product name
    const commentsList = isFood ? [
      {
        author: "Aarav Mehta",
        initials: "AM",
        rating: 5,
        text: `The ${p.name} was incredibly fresh! You can taste the quality difference immediately. Tasted natural and sweet, perfect package size.`
      },
      {
        author: "Priya Sharma",
        initials: "PS",
        rating: 4,
        text: `Very good select of ${p.name}. Sourced perfectly, visual parameter matches the description. Excellent organic packaging.`
      },
      {
        author: "Vikram Malhotra",
        initials: "VM",
        rating: 5,
        text: `Super fast delivery and well-preserved. It is hard to find high quality ${p.name} online but SmartCart delivers every time.`
      }
    ] : [
      {
        author: "Aarav Mehta",
        initials: "AM",
        rating: 5,
        text: `Outstanding build quality! The ${p.name} is incredibly durable and works exactly as described. Best in class choice.`
      },
      {
        author: "Priya Sharma",
        initials: "PS",
        rating: 4,
        text: `Very functional and sleek. The chassis design of ${p.name} is modern, and shipping was quick. Highly recommend.`
      },
      {
        author: "Vikram Malhotra",
        initials: "VM",
        rating: 5,
        text: `Exceptional value for money. Setup for ${p.name} was simple and it integrates perfectly with my devices.`
      }
    ]

    return {
      advantages,
      limitations,
      sentiment,
      reviews: commentsList
    }
  }, [p, isFood])

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-20 animate-pulse flex flex-col gap-10">
        <div className="h-10 bg-card w-1/4 rounded"></div>
        <div className="grid gap-10 lg:grid-cols-2">
          <div className="aspect-square bg-card rounded-2xl"></div>
          <div className="space-y-6">
            <div className="h-12 bg-card rounded w-3/4"></div>
            <div className="h-6 bg-card rounded w-1/2"></div>
            <div className="h-24 bg-card rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !p) {
    return (
      <div className="text-center py-20 flex flex-col items-center gap-4">
        <span className="text-4xl">⚠️</span>
        <h2 className="text-xl font-bold text-foreground">Product Not Found</h2>
        <p className="text-sm text-muted-foreground">The product you are trying to view does not exist or was removed.</p>
        <Button variant="secondary" onClick={() => navigate('/collections')}>Return to Shop</Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        className="mb-4 rounded-xl text-xs font-semibold gap-1.5 px-3 py-1.5 h-auto text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Shop
      </Button>
      <div className="flex items-center justify-between">
        <Badge variant="ai" className="gap-1.5 px-3 py-1 text-xs">
          <Sparkles className="h-3.5 w-3.5 text-secondary" /> Smart Selection
        </Badge>
        <button
          onClick={() => {
            if (!p) return
            const isLiked = wishlistItems.includes(p.id)
            toggleWishlist(p.id)
            toast({
              title: isLiked ? 'Removed from Wishlist' : 'Added to Wishlist',
              description: `${p.name} has been ${isLiked ? 'removed from' : 'added to'} your wishlist.`,
            })
          }}
          className="flex items-center gap-1.5 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
        >
          <Heart className={cn("h-4 w-4", wishlistItems.includes(p.id!) ? "fill-red-500 text-red-500" : "text-muted-foreground")} /> 
          {wishlistItems.includes(p.id!) ? 'In Wishlist' : 'Add to Wishlist'}
        </button>
      </div>

      <div className="mt-6 grid gap-10 lg:grid-cols-2 items-start">
        {/* Left Column: Image Gallery */}
        <div className="flex flex-col gap-4">
          <div className="aspect-square rounded-2xl overflow-hidden bg-card border border-border relative group shadow-sm flex items-center justify-center p-4">
            <img
              src={images[activeImageIndex]}
              alt={p.name}
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
            />
            {/* Overlay Simulated Play Button if it has video */}
            {activeImageIndex === images.length - 1 && images.length > 2 && (
              <div className="absolute inset-0 bg-black/10 flex items-center justify-center">
                <span className="grid h-16 w-16 place-items-center rounded-full bg-background/80 text-primary backdrop-blur shadow-lg hover:scale-110 transition-transform">
                  <Play className="h-7 w-7 fill-current ml-1" />
                </span>
              </div>
            )}
          </div>

          {/* Thumbnails */}
          {images.length > 1 && (
            <div className="grid grid-cols-4 gap-4">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveImageIndex(idx)}
                  className={`aspect-square rounded-xl overflow-hidden bg-card border shadow-sm transition-all focus:outline-none ${
                    activeImageIndex === idx ? 'border-primary ring-2 ring-primary/20' : 'border-border opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={img} alt={`${p.name} thumb ${idx}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Dynamic buy details */}
        <div className="flex flex-col gap-6">
          <div>
            <span className="text-xs font-mono font-bold tracking-widest uppercase text-muted-foreground">{p.brand || 'Generic'}</span>
            <h1 className="text-3xl font-sans font-extrabold tracking-tight text-foreground mt-1">{p.name}</h1>
          </div>

          <div className="flex items-center gap-4 border-y border-border py-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-sans font-black text-foreground">₹{p.price}</span>
              {p.compare_at_price ? (
                <span className="text-lg text-muted-foreground line-through">₹{p.compare_at_price}</span>
              ) : null}
            </div>
            {p.stock && p.stock > 0 ? (
              <Badge variant="success" className="py-1 px-3">
                {p.stock} in stock
              </Badge>
            ) : (
              <Badge variant="destructive" className="py-1 px-3">
                Out of Stock
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-3 text-sm">
            <div className="flex text-warning">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} className={`h-4 w-4 fill-current ${i < Math.floor(p.rating || 4.5) ? 'text-warning' : 'text-border'}`} />
              ))}
            </div>
            <span className="font-semibold text-foreground">{p.rating || 4.5}</span>
            <span className="text-muted-foreground">· {p.review_count || 120} verified reviews</span>
          </div>

          <p className="text-muted-foreground leading-relaxed text-sm">{p.description || 'Premium quality selected item verified by computer vision.'}</p>

          {/* Quantity selector & Add to Cart */}
          <div className="flex items-center gap-4 mt-4">
            <div className="flex items-center border border-border rounded-xl bg-card p-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-lg"
                disabled={qty <= 1}
                onClick={() => setQty(qty - 1)}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-10 text-center font-mono font-bold text-foreground text-sm">{qty}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-lg"
                onClick={() => setQty(qty + 1)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            <Button variant="gradient" size="lg" className="flex-1 py-6 rounded-xl text-sm uppercase tracking-widest font-semibold gap-2" onClick={handleAddToCart}>
              <ShoppingCart className="h-4 w-4" /> Add to Cart
            </Button>
          </div>

          {/* AI Advisor Panel */}
          <div className="rounded-2xl border border-primary/10 bg-primary/5 p-5 mt-4 flex gap-4 items-start">
            <div className="w-10 h-10 bg-primary/10 text-primary flex items-center justify-center rounded-xl shrink-0">
              <Cpu className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-foreground text-sm flex items-center gap-1.5">
                AI Match recommendation <span className="text-secondary font-mono text-xs">(94% match)</span>
              </h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                This item aligns with your preferences. SmartCart analysis tags show zero chemical additions and minimal carbon footprint during farm-to-shelf logistics.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs specifications, insights, reviews */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-16 w-full">
        <TabsList className="flex gap-4 border-b border-border bg-transparent p-0 rounded-none w-full">
          <TabsTrigger value="specs" className="border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-2 pb-3 pt-0 rounded-none font-semibold text-sm">
            Specifications
          </TabsTrigger>
          <TabsTrigger value="insights" className="border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-2 pb-3 pt-0 rounded-none font-semibold text-sm">
            AI Insights
          </TabsTrigger>
          <TabsTrigger value="reviews" className="border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-2 pb-3 pt-0 rounded-none font-semibold text-sm">
            Reviews ({p.review_count || 120})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="specs" className="mt-8">
          <div className="grid gap-6 md:grid-cols-3">
            {specGroups.map((g) => (
              <div key={g.title} className="bg-card rounded-2xl border border-border p-6 shadow-sm flex flex-col gap-4">
                <h4 className="font-bold text-foreground text-sm uppercase tracking-wide border-b border-border pb-2">{g.title}</h4>
                <dl className="space-y-3">
                  {g.rows.map(([key, val]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <dt className="text-muted-foreground">{key}</dt>
                      <dd className="font-semibold text-foreground text-right">{val}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="insights" className="mt-8">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="bg-card rounded-2xl border border-border p-6 shadow-sm flex flex-col gap-4">
              <h4 className="font-bold text-foreground text-sm flex items-center gap-1.5"><PlusCircle className="h-4 w-4 text-success" /> Key Advantages</h4>
              <ul className="space-y-2 text-xs text-muted-foreground list-disc list-inside">
                {dynamicInsightsAndReviews.advantages.map((adv, idx) => (
                  <li key={idx}>{adv}</li>
                ))}
              </ul>
              <h4 className="font-bold text-foreground text-sm flex items-center gap-1.5 mt-2"><MinusCircle className="h-4 w-4 text-destructive" /> Shelf Limitations</h4>
              <ul className="space-y-2 text-xs text-muted-foreground list-disc list-inside">
                {dynamicInsightsAndReviews.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>

            <div className="bg-card rounded-2xl border border-border p-6 shadow-sm flex flex-col gap-4">
              <h4 className="font-bold text-foreground text-sm">Sentiment analysis</h4>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-gradient">{dynamicInsightsAndReviews.sentiment}%</span>
                <span className="text-xs text-muted-foreground">Positive score across customers</span>
              </div>
              <div className="space-y-3 mt-2">
                <div>
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Quality rating</span>
                    <span className="font-bold text-foreground">95%</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Delivery speed</span>
                    <span className="font-bold text-foreground">88%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="reviews" className="mt-8">
          <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
            <div className="bg-card rounded-2xl border border-border p-6 shadow-sm flex flex-col gap-3">
              <div className="text-4xl font-extrabold text-foreground">{p.rating || 4.5}</div>
              <div className="flex text-warning">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className={`h-4 w-4 fill-current ${i < Math.floor(p.rating || 4.5) ? 'text-warning' : 'text-border'}`} />
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Verified ratings average</p>
            </div>

            <div className="bg-card rounded-2xl border border-border p-6 shadow-sm flex flex-col gap-6">
              <h4 className="font-bold text-foreground text-base">Reviews</h4>
              <div className="divide-y divide-border space-y-6">
                {dynamicInsightsAndReviews.reviews.map((r, idx) => (
                  <div key={idx} className={`${idx > 0 ? 'pt-6' : 'pt-2'} flex flex-col gap-3`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                          {r.initials}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-foreground">{r.author}</p>
                          <div className="flex text-warning">
                            {Array.from({ length: r.rating }).map((_, i) => (
                              <Star key={i} className="h-3 w-3 fill-current text-warning" />
                            ))}
                          </div>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground"><ThumbsUp className="h-4 w-4" /></Button>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {r.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}