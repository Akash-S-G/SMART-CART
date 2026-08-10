import { useMemo, useState, useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  Check,
  SlidersHorizontal,
  Sparkles,
  Zap,
  Heart,
  Star,
  ChevronDown,
  Loader2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getCategoriesApi, listAllProductsApi, searchProductsApi } from '@/lib/api'
import { useCart } from '@/hooks/use-cart'
import { useWishlist } from '@/hooks/use-wishlist'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/cn'

const PRICE_FILTERS = [
  { label: 'Under ₹500', min: 0, max: 500 },
  { label: '₹500 - ₹1500', min: 500, max: 1500 },
  { label: 'Over ₹1500', min: 1500, max: 999999 },
]
const SORTS = ['Recommended', 'Price: Low to High', 'Price: High to Low', 'Top Rated']

export function CollectionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const searchQuery = searchParams.get('search') || ''
  const categoryParam = searchParams.get('category') || ''
  const { addItem } = useCart()
  const { items: wishlistItems, toggleItem: toggleWishlist } = useWishlist()
  const { toast } = useToast()

  const [cats, setCats] = useState<string[]>(() => categoryParam ? [categoryParam] : [])
  const [prices, setPrices] = useState<string[]>([])
  const [sort, setSort] = useState('Recommended')
  const BATCH = 12
  const [visibleCount, setVisibleCount] = useState(BATCH)
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (categoryParam && !cats.includes(categoryParam)) {
      setCats([categoryParam])
    }
    setVisibleCount(BATCH)
  }, [categoryParam])

  useEffect(() => {
    setVisibleCount(BATCH)
  }, [searchQuery])

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategoriesApi,
  })

  const { data: products, isLoading } = useQuery({
    queryKey: ['products', searchQuery],
    queryFn: () => (searchQuery ? searchProductsApi(searchQuery) : listAllProductsApi()),
    placeholderData: keepPreviousData,
  })

  const toggle = (list: string[], set: (v: string[]) => void, v: string) => {
    setVisibleCount(BATCH)
    set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v])
  }

  const shown = useMemo(() => {
    if (!products || !Array.isArray(products)) return []
    let result = [...products]

    // Category Filter
    if (cats.length > 0) {
      result = result.filter((p) => cats.includes(p.category_id))
    }

    // Price Filter
    if (prices.length > 0) {
      result = result.filter((p) => {
        return prices.some((pLabel) => {
          const filter = PRICE_FILTERS.find((f) => f.label === pLabel)
          if (!filter) return true
          const price = p.price || 0
          return price >= filter.min && price <= filter.max
        })
      })
    }

    // Sort
    if (sort === 'Price: Low to High') {
      result.sort((a, b) => (a.price || 0) - (b.price || 0))
    } else if (sort === 'Price: High to Low') {
      result.sort((a, b) => (b.price || 0) - (a.price || 0))
    } else if (sort === 'Top Rated') {
      result.sort((a, b) => (b.rating || 0) - (a.rating || 0))
    }

    return result
  }, [products, cats, prices, sort])

  const visibleProducts = useMemo(() => shown.slice(0, Math.min(visibleCount, shown.length)), [shown, visibleCount])
  const hasMore = visibleProducts.length < shown.length

  useEffect(() => {
    const node = sentinelRef.current
    if (!node) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setVisibleCount((v) => v + BATCH)
        }
      },
      { rootMargin: '400px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasMore, BATCH])

  const handleQuickAdd = async (e: React.MouseEvent, productId: string, name: string) => {
    e.preventDefault()
    try {
      await addItem(productId, 1)
      toast({
        title: 'Added to Cart',
        description: `${name} has been added to your shopping cart.`,
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to add item to cart.',
        variant: 'destructive',
      })
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <Badge variant="secondary" className="w-fit gap-1 text-[11px] font-semibold uppercase tracking-wider px-3 py-1">
          <SlidersHorizontal className="h-3 w-3" /> Catalog Directory
        </Badge>
        <h1 className="text-4xl font-sans font-extrabold text-foreground tracking-tight">
          {searchQuery ? `Results for "${searchQuery}"` : 'Browse Grocery Products'}
        </h1>
        <p className="text-sm text-muted-foreground">
          Showing {shown.length} verified grocery items with real-time stock status.
        </p>
      </div>

      {/* Main Layout */}
      <div className="mt-8 grid gap-8 lg:grid-cols-4">
        {/* Sidebar Filters */}
        <div className="space-y-6 lg:col-span-1">
          <div className="bg-card border border-border rounded-3xl p-6 shadow-sm space-y-6 lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto">
            {/* Category Filter */}
            <div>
              <h3 className="font-bold text-foreground text-sm mb-3">Categories</h3>
              <div className="space-y-2">
                {categories?.map((c) => (
                  <FilterRow
                    key={c.id}
                    label={c.name}
                    checked={cats.includes(c.id)}
                    onToggle={() => toggle(cats, setCats, c.id)}
                  />
                ))}
              </div>
            </div>

            {/* Price Filter */}
            <div className="border-t border-black/[0.04] pt-6">
              <h3 className="font-bold text-foreground text-sm mb-3">Price Range</h3>
              <div className="space-y-2">
                {PRICE_FILTERS.map((f) => (
                  <FilterRow
                    key={f.label}
                    label={f.label}
                    checked={prices.includes(f.label)}
                    onToggle={() => toggle(prices, setPrices, f.label)}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Product Grid & Sorting */}
        <div className="lg:col-span-3 space-y-6">
          {/* Controls Bar */}
          <div className="flex justify-between items-center bg-card border border-border rounded-2xl px-5 py-3 shadow-sm">
            <span className="text-xs font-semibold text-muted-foreground">
              Showing {visibleProducts.length} of {shown.length} items
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-foreground">Sort By:</span>
              <div className="flex gap-1">
                {SORTS.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setSort(s); setVisibleCount(BATCH); }}
                    className={`text-[11px] font-bold px-3 py-1.5 rounded-xl transition ${
                      sort === s ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.04]'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse bg-card rounded-3xl p-4 border border-border h-96"></div>
              ))}
            </div>
          ) : visibleProducts.length === 0 ? (
            <div className="text-center py-20 bg-card/20 rounded-3xl border border-dashed border-border flex flex-col items-center justify-center gap-4">
              <span className="text-4xl">🔎</span>
              <h3 className="text-lg font-bold text-foreground">No Products Found</h3>
              <p className="text-sm text-muted-foreground max-w-xs">
                We couldn't find any products matching your filters or search query.
              </p>
              <Button variant="secondary" onClick={() => { setCats([]); setPrices([]); }}>
                Reset Filters
              </Button>
            </div>
          ) : (
            <>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {visibleProducts.map((p, idx) => (
                  <ProductCard key={p.id} p={p} index={idx} handleQuickAdd={handleQuickAdd} />
                ))}
              </div>

              {/* Page Pagination Controls */}
              <div ref={sentinelRef} className={hasMore ? 'flex h-16 items-center justify-center' : undefined}>
                {hasMore && <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />}
              </div>
              {!hasMore && (
                <div className="mt-4 pt-6 border-t border-border text-center">
                  <p className="text-xs font-semibold text-muted-foreground">
                    You've reached the end — {shown.length} products shown.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function FilterRow({
  label,
  checked,
  onToggle,
}: {
  label: string
  checked: boolean
  onToggle: () => void
}) {
  return (
    <button
      onClick={onToggle}
      className="flex w-full items-center gap-2.5 text-left text-sm transition hover:text-foreground"
    >
      <span
        className={`grid h-5 w-5 place-items-center rounded-[5px] border transition ${
          checked
            ? 'border-primary bg-primary text-primary-foreground'
            : 'border-black/20 text-transparent'
        }`}
      >
        <Check className="h-3.5 w-3.5" />
      </span>
      <span className={checked ? 'text-foreground font-semibold' : 'text-muted-foreground'}>{label}</span>
    </button>
  )
}

function ProductCard({
  p,
  index,
  handleQuickAdd,
}: {
  p: Product
  index: number
  handleQuickAdd: (e: React.MouseEvent, productId: string, name: string) => void
}) {
  const { items: wishlistItems, toggleItem: toggleWishlist } = useWishlist()
  const { toast } = useToast()
  const thumbnail = p.images?.[0] || 'https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80'

  return (
    <Link
      to={`/product/${p.id}`}
      className="group flex flex-col gap-4 bg-card p-4 border border-border rounded-3xl hover:border-primary/40 hover:shadow-xl transition-all duration-300 cursor-pointer"
    >
      <div className="relative w-full aspect-[4/5] bg-surface-container-low overflow-hidden rounded-2xl">
        <img
          src={thumbnail}
          alt={p.name}
          className="h-full w-full object-cover transition duration-700 group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute left-3 top-3 flex flex-col gap-2">
          {p.compare_at_price ? (
            <Badge variant="warning" className="font-semibold">
              Save {Math.round((1 - (p.price ?? 0) / p.compare_at_price) * 100)}%
            </Badge>
          ) : null}
          {index % 4 === 0 && (
            <Badge variant="ai" className="gap-1 shadow-sm font-semibold">
              <Sparkles className="h-3 w-3 text-secondary" /> Top Pick
            </Badge>
          )}
        </div>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            const isLiked = wishlistItems.includes(p.id)
            toggleWishlist(p.id)
            toast({
              title: isLiked ? 'Removed from Wishlist' : 'Added to Wishlist',
              description: `${p.name} has been ${isLiked ? 'removed from' : 'added to'} your wishlist.`,
            })
          }}
          aria-label="Wishlist"
          className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-black/40 text-white/80 backdrop-blur transition hover:bg-black/60 hover:text-white"
        >
          <Heart className={cn("h-4 w-4", wishlistItems.includes(p.id) ? "fill-red-500 text-red-500" : "text-white/80")} />
        </button>
        {p.stock === 0 && (
          <div className="absolute inset-x-0 bottom-0 bg-black/70 p-3 text-center text-sm font-medium text-white backdrop-blur">
            Out of Stock
          </div>
        )}
        {p.stock !== 0 && (
          <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-4">
            <button
              onClick={(e) => handleQuickAdd(e, p.id, p.name)}
              className="bg-primary text-primary-foreground px-6 py-2.5 rounded-full font-semibold text-xs uppercase tracking-widest translate-y-4 group-hover:translate-y-0 transition-transform shadow-lg hover:bg-secondary"
            >
              Quick Add
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-1 px-1">
        <div className="flex justify-between items-start gap-4">
          <h3 className="text-base font-bold text-foreground truncate group-hover:text-primary transition-colors">{p.name}</h3>
          <span className="text-base font-extrabold text-foreground">₹{p.price}</span>
        </div>
        <div className="flex justify-between items-center mt-1">
          <p className="text-xs text-muted-foreground truncate">{p.brand || 'Premium Selection'}</p>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Star className="h-3.5 w-3.5 fill-warning text-warning" />
            {p.rating || 4.5}
          </span>
        </div>
        {/* Stock indicator */}
        {typeof p.stock === 'number' && (
          <div className="mt-1">
            {p.stock === 0 ? (
              <span className="text-[10px] font-semibold text-red-500 bg-red-500/10 px-2 py-0.5 rounded-full">Out of Stock</span>
            ) : p.stock <= 5 ? (
              <span className="text-[10px] font-semibold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full">Only {p.stock} left!</span>
            ) : (
              <span className="text-[10px] font-semibold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">In Stock</span>
            )}
          </div>
        )}
      </div>
    </Link>
  )
}