import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listOrdersApi, getOrderApi, cancelOrderApi } from '@/lib/api'
import { useAuth } from '@/hooks/use-auth'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Package,
  CheckCircle,
  Truck,
  Home,
  Clock,
  XCircle,
  ChevronDown,
  ChevronUp,
  ShoppingBag,
} from 'lucide-react'

// ─── Status helpers ──────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ComponentType<any> }> = {
  pending:    { label: 'Pending',    color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',  icon: Clock },
  confirmed:  { label: 'Confirmed',  color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',        icon: CheckCircle },
  paid:       { label: 'Paid',       color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: CheckCircle },
  processing: { label: 'Processing', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30',  icon: Package },
  shipped:    { label: 'Shipped',    color: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',  icon: Truck },
  delivered:  { label: 'Delivered',  color: 'bg-green-500/20 text-green-400 border-green-500/30',    icon: Home },
  completed:  { label: 'Completed',  color: 'bg-green-500/20 text-green-400 border-green-500/30',    icon: CheckCircle },
  cancelled:  { label: 'Cancelled',  color: 'bg-red-500/20 text-red-400 border-red-500/30',          icon: XCircle },
  refunded:   { label: 'Refunded',   color: 'bg-gray-500/20 text-gray-400 border-gray-500/30',       icon: XCircle },
}

const TRACKING_STEPS = [
  { key: 'pending',    label: 'Order Placed',   icon: ShoppingBag },
  { key: 'confirmed',  label: 'Confirmed',       icon: CheckCircle },
  { key: 'processing', label: 'Processing',      icon: Package },
  { key: 'shipped',    label: 'Shipped',         icon: Truck },
  { key: 'delivered',  label: 'Delivered',       icon: Home },
]

const STEP_ORDER = ['pending', 'confirmed', 'paid', 'processing', 'shipped', 'delivered', 'completed']

function getStepIndex(status: string) {
  const idx = STEP_ORDER.indexOf(status)
  return idx === -1 ? 0 : idx
}

// ─── Components ──────────────────────────────────────────────────────────────

function TrackingTimeline({ status }: { status: string }) {
  const currentIdx = getStepIndex(status)
  const isCancelled = status === 'cancelled' || status === 'refunded'

  if (isCancelled) {
    return (
      <div className="flex items-center gap-3 py-4 text-red-400">
        <XCircle className="w-6 h-6" />
        <span className="font-medium">
          Order {status === 'refunded' ? 'Refunded' : 'Cancelled'}
        </span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-0 mt-4 overflow-x-auto pb-2">
      {TRACKING_STEPS.map((step, idx) => {
        const done = idx <= currentIdx
        const active = idx === currentIdx
        const Icon = step.icon
        return (
          <div key={step.key} className="flex items-center flex-1 min-w-0">
            <div className="flex flex-col items-center flex-shrink-0">
              <div className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all ${
                done
                  ? 'bg-emerald-500 border-emerald-500 text-white'
                  : 'bg-white/5 border-white/20 text-white/30'
              } ${active ? 'ring-4 ring-emerald-500/30' : ''}`}>
                <Icon className="w-4 h-4" />
              </div>
              <span className={`text-xs mt-1 text-center whitespace-nowrap ${done ? 'text-emerald-400' : 'text-white/30'}`}>
                {step.label}
              </span>
            </div>
            {idx < TRACKING_STEPS.length - 1 && (
              <div className={`h-0.5 flex-1 mx-1 mb-5 ${
                idx < currentIdx ? 'bg-emerald-500' : 'bg-white/10'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

function OrderCard({ order }: { order: any }) {
  const [expanded, setExpanded] = useState(false)
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const cfg = STATUS_CONFIG[order.status] ?? STATUS_CONFIG.pending
  const Icon = cfg.icon

  const cancelMutation = useMutation({
    mutationFn: () => cancelOrderApi(order.id),
    onSuccess: () => {
      toast({ title: 'Order cancelled', description: 'Your order has been cancelled.' })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
    onError: () => toast({ title: 'Error', description: 'Could not cancel order.', variant: 'destructive' }),
  })

  return (
    <div className="rounded-3xl border border-border bg-card shadow-sm overflow-hidden hover:border-primary/20 transition-all">
      {/* Header */}
      <div
        className="flex items-center justify-between p-5 cursor-pointer select-none"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex flex-col gap-1">
          <span className="font-semibold text-foreground text-sm">#{order.order_number}</span>
          <span className="text-xs text-muted-foreground">
            {new Date(order.created_at).toLocaleDateString('en-IN', {
              day: 'numeric', month: 'short', year: 'numeric',
            })}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium px-3 py-1 rounded-full border flex items-center gap-1.5 ${cfg.color}`}>
            <Icon className="w-3.5 h-3.5" />
            {cfg.label}
          </span>
          <span className="text-foreground font-semibold">₹{Number(order.total_amount).toLocaleString('en-IN')}</span>
          {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-white/10 p-5 space-y-4">
          {/* Tracking */}
          <TrackingTimeline status={order.status} />

          {/* Items */}
          {order.items && order.items.length > 0 && (
            <div className="space-y-2 mt-4">
              <p className="text-xs text-white/50 uppercase tracking-wider font-medium">Items</p>
              {order.items.map((item: any) => (
                <div key={item.id} className="flex items-center justify-between text-sm">
                  <span className="text-white/80">{item.product_name} <span className="text-white/40">× {item.quantity}</span></span>
                  <span className="text-white/60">₹{Number(item.total_price).toLocaleString('en-IN')}</span>
                </div>
              ))}
            </div>
          )}

          {/* Totals */}
          <div className="border-t border-white/10 pt-3 space-y-1 text-sm">
            <div className="flex justify-between text-white/60">
              <span>Subtotal</span>
              <span>₹{Number(order.subtotal).toLocaleString('en-IN')}</span>
            </div>
            {Number(order.tax) > 0 && (
              <div className="flex justify-between text-white/60">
                <span>Tax</span>
                <span>₹{Number(order.tax).toLocaleString('en-IN')}</span>
              </div>
            )}
            <div className="flex justify-between font-semibold text-white pt-1">
              <span>Total</span>
              <span>₹{Number(order.total_amount).toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Actions */}
          {order.status === 'pending' && (
            <Button
              variant="outline"
              size="sm"
              className="border-red-500/40 text-red-400 hover:bg-red-500/10 hover:border-red-500/60"
              onClick={(e) => { e.stopPropagation(); cancelMutation.mutate() }}
              disabled={cancelMutation.isPending}
            >
              <XCircle className="w-4 h-4 mr-2" />
              {cancelMutation.isPending ? 'Cancelling…' : 'Cancel Order'}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function OrdersPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['orders', page],
    queryFn: () => listOrdersApi(page, 10),
    enabled: !!user,
  })

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <ShoppingBag className="w-16 h-16 text-white/20 mx-auto" />
          <p className="text-white/60">Sign in to view your orders.</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 py-10">
      <div className="max-w-3xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-white/70 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">My Orders</h1>
            <p className="text-white/50 text-sm">Track and manage your purchases</p>
          </div>
        </div>

        {/* Orders list */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 rounded-2xl bg-white/5 border border-white/10 animate-pulse" />
            ))}
          </div>
        ) : !data?.items?.length ? (
          <div className="text-center py-20">
            <ShoppingBag className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <p className="text-white/50 text-lg">No orders yet</p>
            <p className="text-white/30 text-sm mb-6">Start shopping to see your orders here.</p>
            <Button onClick={() => navigate('/collections')}>Browse Products</Button>
          </div>
        ) : (
          <div className="space-y-4">
            {data.items.map((order: any) => (
              <OrderCard key={order.id} order={order} />
            ))}

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-center gap-3 pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="border-white/20 text-white/70 hover:bg-white/10"
                >
                  Previous
                </Button>
                <span className="text-white/50 text-sm">Page {page} of {data.total_pages}</span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === data.total_pages}
                  onClick={() => setPage(p => p + 1)}
                  className="border-white/20 text-white/70 hover:bg-white/10"
                >
                  Next
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
