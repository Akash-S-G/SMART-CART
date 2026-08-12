import { useMemo, useState, useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery, useInfiniteQuery, keepPreviousData } from '@tanstack/react-query'
import {
  Check,
  SlidersHorizontal,
  Sparkles,
  Heart,
  Star,
  Loader2,
  ShoppingCart,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getCategoriesApi, fetchProductsPageApi, searchProductsApi } from '@/lib/api'
import type { Product } from '@/types/api'
import { useCart } from '@/hooks/use-cart'
import { useWishlist } from '@/hooks/use-wishlist'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/cn'

const PRICE_FILTERS = [
  { label: 'Under ₹500', min: 0, max: 500 },
  { label: '₹500 - ₹1500', min: 500, max: 1500 },
  { label: 'Over ₹1500', min: 1500, max: 999999 },
]
const SORTS: { label: string; value: string }[] = [
  { label: 'Recommended', value: '' },
  { label: 'Price: Low to High', value: 'price_asc' },
  { label: 'Price: High to Low', value: 'price_desc' },
  { label: 'Top Rated', value: 'rating_desc' },
]

const PAGE_SIZE = 24

export function CollectionsPage() {
  const searchParams = useSearchParams()[0]
  const searchQuery = searchParams.get('search') || ''
  const categoryParam = searchParams.get('category') || ''
  const { addItem } = useCart()
  const { items: wishlistItems, toggleItem: toggleWishlist } = useWishlist()
  const { toast } = useToast()

  const [cats, setCats] = useState<string[]>(() => (categoryParam ? [categoryParam] : []))
  const [prices, setPrices] = useState<string[]>([])
  const [sort, setSort] = useState('')
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (categoryParam && !cats.includes(categoryParam)) {
      setCats([categoryParam])
    }
  }, [categoryParam])

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategoriesApi,
  })

  // Build a stable filter signature so each filter change resets pagination.
  const filterKey = JSON.stringify({ searchQuery, cats, prices, sort })

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['products-infinite', filterKey],
    initialPageParam: 0,
    queryFn: ({ pageParam }) => {
      if (searchQuery) {
        return searchProductsApi(searchQuery)
      }
      const price = prices.length === 1 ? PRICE_FILTERS.find((f) => f.label === prices[0]) : undefined
      return fetchProductsPageApi({
        skip: pageParam,
        limit: PAGE_SIZE,
        category_id: cats.length === 1 ? cats[0] : cats.length > 1 ? undefined : undefined,
        min_price: price?.min,
        max_price: price?.max,
        sort: sort || undefined,
      })
    },
    getNextPageParam: (lastPage, allPages) => {
      // No total count from backend; stop when a page returns fewer than PAGE_SIZE.
      if (!lastPage || lastPage.length < PAGE_SIZE) return undefined
      return allPages.length * PAGE_SIZE
    },
  })

  const products = useMemo(() => (data ? data.pages.flat() : []), [data])
  const loadedCount = products.length

  const toggle = (list: string[], set: (v: string[]) => void, v: string) => {
    set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v])
  }

  // Auto-load more when the sentinel scrolls into view (bonus on top of the button).
  useEffect(() => {
    const node = sentinelRef.current
    if (!node || !hasNextPage || isFetchingNextPage) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) fetchNextPage()
      },
      { rootMargin: '600px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

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
          {isLoading ? 'Loading products…' : `Showing ${loadedCount} verified grocery items with real-time stock status.`}
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
              {loadedCount} {loadedCount === 1 ? 'item' : 'items'} loaded
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-foreground">Sort By:</span>
              <div className="flex gap-1">
                {SORTS.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setSort(s.value)}
                    className={`text-[11px] font-bold px-3 py-1.5 rounded-xl transition ${
                      sort === s.value ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.04]'
                    }`}
                  >
                    {s.label}
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
          ) : isError ? (
            <div className="text-center py-20 bg-card/20 rounded-3xl border border-dashed border-border">
              <p className="text-sm text-muted-foreground">Failed to load products. Please try again.</p>
              <Button variant="secondary" className="mt-4" onClick={() => fetchNextPage()}>Retry</Button>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-20 bg-card/20 rounded-3xl border border-dashed border-border flex flex-col items-center justify-center gap-4">
              <span className="text-4xl">🔎</span>
              <h3 className="text-lg font-bold text-foreground">No Products Found</h3>
              <p className="text-sm text-muted-foreground max-w-xs">
                We couldn't find any products matching your filters or search query.
              </p>
              <Button variant="secondary" onClick={() => { setCats([]); setPrices([]) }}>
                Reset Filters
              </Button>
            </div>
          ) : (
            <>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {products.map((p, idx) => (
                  <ProductCard key={p.id} p={p} index={idx} handleQuickAdd={handleQuickAdd} />
                ))}
              </div>

              {/* Load More + sentinel */}
              <div className="mt-8 flex flex-col items-center gap-4">
                <div ref={sentinelRef} className="h-px w-full" />
                {hasNextPage ? (
                  <Button
                    variant="outline"
                    className="rounded-xl px-8 py-6 font-semibold"
                    onClick={() => fetchNextPage()}
                    disabled={isFetchingNextPage}
                  >
                    {isFetchingNextPage ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
                      </>
                    ) : (
                      <>Load More Products</>
                    )}
                  </Button>
                ) : (
                  <p className="text-xs font-semibold text-muted-foreground">
                    You've reached the end — {loadedCount} products shown.
                  </p>
                )}
              </div>
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
          checked ? 'border-primary bg-primary text-primary-foreground' : 'border-black/20 text-transparent'
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
      className="group flex flex-col justify-between bg-card p-4 border border-border rounded-3xl hover:border-primary/40 hover:shadow-xl transition-all duration-300 cursor-pointer"
    >
      {/* 1. Clean Product Image Container */}
      <div className="relative w-full aspect-[4/5] bg-surface-container-low overflow-hidden rounded-2xl border border-black/5 shrink-0">
        <img
          src={thumbnail}
          alt={p.name}
          className="h-full w-full object-cover transition duration-700 group-hover:scale-105"
          loading="lazy"
        />
      </div>

      {/* 2. Details & Controls Container (All labels and buttons outside image) */}
      <div className="flex flex-col gap-2 pt-3 px-1 flex-1 justify-between">
        {/* Top Badges & Wishlist Action Row */}
        <div className="flex items-center justify-between gap-2 flex-wrap min-h-[26px]">
          <div className="flex items-center gap-1.5 flex-wrap">
            {p.compare_at_price ? (
              <Badge variant="warning" className="font-semibold text-[10px] py-0.5 px-2">
                Save {Math.round((1 - (p.price ?? 0) / p.compare_at_price) * 100)}%
              </Badge>
            ) : null}
            {index % 3 === 0 && (
              <Badge variant="ai" className="gap-1 shadow-xs font-semibold text-[10px] py-0.5 px-2">
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
            className="p-1.5 rounded-full hover:bg-black/5 text-muted-foreground transition"
          >
            <Heart className={cn('h-4 w-4', wishlistItems.includes(p.id) ? 'fill-red-500 text-red-500' : 'text-muted-foreground')} />
          </button>
        </div>

        {/* Product Title & Brand */}
        <div>
          <h3 className="text-base font-bold text-foreground truncate group-hover:text-primary transition-colors">{p.name}</h3>
          <p className="text-xs text-muted-foreground truncate">{p.brand || 'SmartCart Essentials'}</p>
        </div>

        {/* Price & Rating Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-extrabold text-foreground">₹{p.price}</span>
            {p.compare_at_price ? (
              <span className="text-xs text-muted-foreground line-through">₹{p.compare_at_price}</span>
            ) : null}
          </div>
          <span className="flex items-center gap-1 text-xs font-semibold text-foreground">
            <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
            {p.rating || 4.5}
          </span>
        </div>

        {/* Stock Label & Add to Cart Button Row */}
        <div className="flex items-center justify-between gap-2 pt-2 border-t border-border/60 mt-1">
          {typeof p.stock === 'number' && (
            <div>
              {p.stock === 0 ? (
                <span className="text-[10px] font-bold text-destructive bg-destructive/10 px-2 py-1 rounded-full uppercase tracking-wider">Out of Stock</span>
              ) : p.stock <= 5 ? (
                <span className="text-[10px] font-bold text-amber-600 bg-amber-500/10 px-2 py-1 rounded-full uppercase tracking-wider">Only {p.stock} left</span>
              ) : (
                <span className="text-[10px] font-bold text-emerald-600 bg-emerald-500/10 px-2 py-1 rounded-full uppercase tracking-wider">In Stock</span>
              )}
            </div>
          )}

          <Button
            size="sm"
            variant={p.stock === 0 ? "outline" : "gradient"}
            disabled={p.stock === 0}
            onClick={(e) => handleQuickAdd(e, p.id, p.name)}
            className="rounded-xl text-xs font-bold uppercase tracking-wider h-8 px-3 gap-1 shadow-xs"
          >
            <ShoppingCart className="h-3.5 w-3.5" /> Add
          </Button>
        </div>
      </div>
    </Link>
  )
}
