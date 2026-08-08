import { useState } from 'react'
import { Sparkles, ShoppingBag, X, ChefHat, Check, ArrowRight, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useCart } from '@/hooks/use-cart'
import { useAuth } from '@/hooks/use-auth'
import { useToast } from '@/components/ui/use-toast'
import { listProductsApi, searchProductsApi } from '@/lib/api'
import type { Product } from '@/types/api'

interface RecipePreset {
  id: string
  title: string
  emoji: string
  servings: string
  time: string
  ingredients: string[]
}

const PRESET_RECIPES: RecipePreset[] = [
  {
    id: 'butter-chicken',
    title: 'Butter Chicken & Naan',
    emoji: '🍛',
    servings: '4 Servings',
    time: '35 mins',
    ingredients: ['Chicken', 'Butter', 'Cream', 'Tomato', 'Spices'],
  },
  {
    id: 'creamy-pasta',
    title: 'Creamy Garlic Pasta',
    emoji: '🍝',
    servings: '2 Servings',
    time: '20 mins',
    ingredients: ['Pasta', 'Cream', 'Cheese', 'Butter', 'Garlic'],
  },
  {
    id: 'protein-salad',
    title: 'Fresh Paneer Protein Salad',
    emoji: '🥗',
    servings: '2 Servings',
    time: '15 mins',
    ingredients: ['Paneer', 'Tomato', 'Cucumber', 'Butter', 'Salad'],
  },
  {
    id: 'quick-breakfast',
    title: 'Healthy Morning Breakfast',
    emoji: '🍳',
    servings: '2 Servings',
    time: '10 mins',
    ingredients: ['Milk', 'Bread', 'Butter', 'Fruit', 'Juice'],
  },
]

export function AICopilot() {
  const [isOpen, setIsOpen] = useState(false)
  const [customPrompt, setCustomPrompt] = useState('')
  const [activeRecipe, setActiveRecipe] = useState<RecipePreset | null>(PRESET_RECIPES[0])
  const [matchedProducts, setMatchedProducts] = useState<Product[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isAdding, setIsAdding] = useState(false)

  const { addItem } = useCart()
  const { openLogin, user } = useAuth()
  const { toast } = useToast()

  const findIngredients = async (keywords: string[]) => {
    setIsSearching(true)
    try {
      const allCatalog = await listProductsApi(0, 200)
      const matched: Product[] = []
      const usedIds = new Set<string>()

      for (const kw of keywords) {
        const found = allCatalog.find(
          (p) =>
            !usedIds.has(p.id) &&
            (p.name.toLowerCase().includes(kw.toLowerCase()) ||
              (p.brand && p.brand.toLowerCase().includes(kw.toLowerCase())))
        )
        if (found) {
          usedIds.add(found.id)
          matched.push(found)
        }
      }

      // Fill remaining if needed
      if (matched.length === 0) {
        setMatchedProducts(allCatalog.slice(0, 4))
      } else {
        setMatchedProducts(matched)
      }
    } catch {
      // Fallback
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectPreset = (preset: RecipePreset) => {
    setActiveRecipe(preset)
    findIngredients(preset.ingredients)
  }

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!customPrompt.trim()) return

    setIsSearching(true)
    setActiveRecipe(null)
    try {
      const results = await searchProductsApi(customPrompt.trim())
      if (results && results.length > 0) {
        setMatchedProducts(results.slice(0, 4))
      } else {
        const keywords = customPrompt.split(' ')
        await findIngredients(keywords)
      }
    } catch {
      // Fallback
    } finally {
      setIsSearching(false)
    }
  }

  const handleAddAllToCart = async () => {
    if (!user) {
      openLogin()
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to add recipe ingredients to your cart.',
      })
      return
    }

    if (matchedProducts.length === 0) return

    setIsAdding(true)
    try {
      for (const p of matchedProducts) {
        await addItem(p.id, 1)
      }
      toast({
        title: 'Recipe Ingredients Added! 🛒',
        description: `Successfully added ${matchedProducts.length} items to your shopping cart.`,
      })
      setIsOpen(false)
    } catch {
      toast({
        title: 'Cart Error',
        description: 'Failed to add recipe items to cart.',
        variant: 'destructive',
      })
    } finally {
      setIsAdding(false)
    }
  }

  const recipeTotal = matchedProducts.reduce((sum, p) => sum + (p.price || 0), 0)

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => {
          setIsOpen(true)
          if (matchedProducts.length === 0 && activeRecipe) {
            findIngredients(activeRecipe.ingredients)
          }
        }}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 bg-gradient-to-r from-primary via-emerald-600 to-teal-500 text-primary-foreground px-5 py-3.5 rounded-full shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 border border-white/20 group"
      >
        <div className="relative">
          <ChefHat className="h-5 w-5 group-hover:rotate-12 transition-transform" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
          </span>
        </div>
        <span className="font-sans font-bold text-xs uppercase tracking-wider">AI Recipe Copilot</span>
      </button>

      {/* Slide-over Drawer Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="relative w-full max-w-md bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300">
            {/* Header */}
            <div className="p-6 border-b border-border bg-black/[0.02] flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-primary/10 text-primary rounded-2xl">
                  <ChefHat className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="font-extrabold text-foreground text-lg flex items-center gap-2">
                    Smart AI Chef <Sparkles className="h-4 w-4 text-amber-500" />
                  </h2>
                  <p className="text-xs text-muted-foreground">Type a dish to auto-load available ingredients into your cart.</p>
                </div>
              </div>
              <Button variant="ghost" size="icon" className="rounded-full h-9 w-9" onClick={() => setIsOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Recipe Prompt Form */}
              <form onSubmit={handleCustomSubmit} className="relative">
                <Input
                  type="text"
                  placeholder="e.g. Ingredients for Tacos, Biryani, Salad..."
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  className="pl-4 pr-12 py-6 rounded-2xl border-border bg-background text-sm shadow-sm"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSearching}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl h-9 w-9 p-0"
                >
                  {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                </Button>
              </form>

              {/* Preset Recipes */}
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3 block">
                  Featured Quick Recipes
                </span>
                <div className="grid grid-cols-2 gap-2.5">
                  {PRESET_RECIPES.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => handleSelectPreset(r)}
                      className={`p-3.5 rounded-2xl border text-left transition-all ${
                        activeRecipe?.id === r.id
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border bg-background hover:border-black/20'
                      }`}
                    >
                      <div className="text-xl mb-1">{r.emoji}</div>
                      <div className="font-bold text-xs text-foreground truncate">{r.title}</div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">{r.time} · {r.servings}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Matched Ingredients Catalog Items */}
              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                    Matched Pantry Items ({matchedProducts.length})
                  </span>
                  {isSearching && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />}
                </div>

                {matchedProducts.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-border rounded-2xl text-muted-foreground text-xs">
                    Searching catalog for ingredients...
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {matchedProducts.map((p) => (
                      <div key={p.id} className="flex items-center gap-3 p-3 bg-background border border-border rounded-2xl shadow-sm">
                        <img
                          src={p.images?.[0] || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=100'}
                          alt={p.name}
                          className="h-12 w-12 rounded-xl object-cover border border-border"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-xs text-foreground truncate">{p.name}</h4>
                          <span className="text-[10px] text-muted-foreground block">{p.brand || 'Fresh Product'}</span>
                        </div>
                        <div className="font-bold text-xs text-foreground">₹{p.price}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer Action Bar */}
            <div className="p-6 border-t border-border bg-black/[0.02] space-y-3">
              <div className="flex justify-between items-center text-xs font-bold text-foreground">
                <span>Ingredient Subtotal:</span>
                <span className="text-base text-primary font-black">₹{recipeTotal.toLocaleString()}</span>
              </div>
              <Button
                variant="gradient"
                disabled={isAdding || matchedProducts.length === 0}
                onClick={handleAddAllToCart}
                className="w-full py-6 rounded-2xl font-bold uppercase text-xs tracking-wider gap-2 shadow-lg"
              >
                {isAdding ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Adding to Cart...
                  </>
                ) : (
                  <>
                    <ShoppingBag className="h-4 w-4" /> Add All {matchedProducts.length} Recipe Items to Cart
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
