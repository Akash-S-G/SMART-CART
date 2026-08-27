import { useState, useEffect } from 'react'
import type { ComponentProps } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Check,
  ArrowRight,
  Lock,
  CreditCard,
  Apple,
  Landmark,
  MapPin,
  Mail,
  Minus,
  Plus,
  Store,
  ArrowLeft,
  ChevronRight,
  Sparkles,
  ShoppingBag,
  Loader2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useCart } from '@/hooks/use-cart'
import { checkoutApi, createPaymentApi, verifyPaymentApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import type { Order, PaymentMethod } from '@/types/api'

const STEPS = ['Shipping', 'Payment', 'Review']

export function CheckoutPage() {
  const navigate = useNavigate()
  const { isAuthenticated, user, openLogin } = useAuth()
  const { cart, fetchCart, updateItem, removeItem, setCart, loading: cartLoading } = useCart()
  const { toast } = useToast()

  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [completedOrder, setCompletedOrder] = useState<Order | null>(null)

  // Form states pre-filled with user info if available
  const [shippingForm, setShippingForm] = useState({
    firstName: user?.first_name || user?.username || '',
    lastName: user?.last_name || '',
    address: '',
    city: '',
    state: '',
    zip: '',
    country: 'India',
    email: user?.email || '',
    phone: '',
  })

  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242')
  const [expiry, setExpiry] = useState('12 / 29')
  const [cvv, setCvv] = useState('123')
  const [cardName, setCardName] = useState('')
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('card')

  // Derived cart summary used by the order-summary sidebar.
  const summary = cart?.summary

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart()
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (user) {
      setShippingForm((f) => ({
        ...f,
        firstName: f.firstName || user.first_name || user.username || '',
        lastName: f.lastName || user.last_name || '',
        email: f.email || user.email || '',
      }))
    }
  }, [user])

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center flex flex-col items-center justify-center gap-6">
        <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center">
          <Lock className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Sign In to Checkout</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          You must be logged in to view your shopping cart, manage addresses, and process payments securely.
        </p>
        <Button variant="gradient" size="lg" className="w-full rounded-xl py-6" onClick={() => openLogin()}>
          Sign In / Register
        </Button>
      </div>
    )
  }

  if (completedOrder) {
    return <OrderConfirmationScreen order={completedOrder} address={shippingForm} />
  }

  // If cart is currently loading, show loading screen instead of premature empty cart
  if (cartLoading && !cart) {
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center flex flex-col items-center justify-center gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-sm font-semibold text-muted-foreground">Loading your shopping cart…</p>
      </div>
    )
  }

  const items = cart?.items || []
  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center flex flex-col items-center justify-center gap-6">
        <div className="w-16 h-16 bg-muted text-muted-foreground rounded-full flex items-center justify-center">
          <ShoppingBag className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Your Cart is Empty</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Add items to your cart from our premium collections or scan them using the AI Vision Scanner to proceed.
        </p>
        <Button variant="secondary" className="w-full rounded-xl py-6" onClick={() => navigate('/collections')}>
          Browse Shop
        </Button>
      </div>
    )
  }

  const next = () => setStep((s) => Math.min(s + 1, 2))
  const back = () => setStep((s) => Math.max(s - 1, 0))

  const handlePlaceOrder = async () => {
    setLoading(true)
    try {
      // 1. Checkout Cart to create Order
      const checkoutRes = await checkoutApi()
      const order = checkoutRes.order

      // 2. Create Payment
      const paymentRes = await createPaymentApi(order.id, selectedMethod)

      // 3. Verify Payment (simulates transaction confirmation)
      await verifyPaymentApi(paymentRes.transaction_id)

      // 4. Update local state
      setCart(null) // Clear cart state
      setCompletedOrder(order)
      toast({
        title: 'Order Placed!',
        description: `Order ${order.order_number} has been processed successfully.`,
      })
    } catch (err: any) {
      toast({
        title: 'Transaction Failed',
        description: err.message || 'There was an issue processing your order.',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        className="mb-4 rounded-xl text-xs font-semibold gap-1.5 px-3 py-1.5 h-auto text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </Button>
      <h1 className="text-3xl font-sans font-extrabold tracking-tight text-foreground">Checkout</h1>

      {/* Stepper */}
      <ol className="mt-6 flex items-center gap-4">
        {STEPS.map((s, i) => (
          <li key={s} className="flex flex-1 items-center gap-4">
            <span
              className={cn(
                'grid h-9 w-9 shrink-0 place-items-center rounded-full border text-xs font-bold transition',
                i < step
                  ? 'border-primary bg-primary text-primary-foreground'
                  : i === step
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border text-muted-foreground',
              )}
            >
              {i < step ? <Check className="h-4 w-4" /> : i + 1}
            </span>
            <span className={cn('text-xs font-bold tracking-wider uppercase', i === step ? 'text-foreground' : 'text-muted-foreground')}>
              {s}
            </span>
            {i < STEPS.length - 1 && <span className="hidden h-px flex-1 bg-black/10 sm:block" />}
          </li>
        ))}
      </ol>

      <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_400px] items-start">
        {/* Main Step content */}
        <div>
          {step === 0 && (
            <StepShipping
              form={shippingForm}
              setForm={setShippingForm}
              onContinue={next}
            />
          )}
          {step === 1 && (
            <StepPayment
              cardNumber={cardNumber}
              setCardNumber={setCardNumber}
              expiry={expiry}
              setExpiry={setExpiry}
              cvv={cvv}
              setCvv={setCvv}
              cardName={cardName}
              setCardName={setCardName}
              selectedMethod={selectedMethod}
              setSelectedMethod={setSelectedMethod}
              onBack={back}
              onReview={next}
            />
          )}
          {step === 2 && (
            <StepReview
              shippingForm={shippingForm}
              cardNumber={cardNumber}
              selectedMethod={selectedMethod}
              cart={cart}
              loading={loading}
              onBack={back}
              onPlace={handlePlaceOrder}
            />
          )}
        </div>

        {/* Order Summary Sidebar */}
        <OrderSummary
          cart={cart}
          summary={summary}
          step={step}
          updateItem={updateItem}
          removeItem={removeItem}
        />
      </div>

      <div className="mt-10 flex items-center justify-center gap-2 text-xs text-muted-foreground uppercase tracking-wider">
        <Lock className="h-4 w-4 text-success" />
        <span>256-Bit SSL Secured Encryption Gateway</span>
      </div>
    </div>
  )
}

/* Shipping Step */
function StepShipping({
  form,
  setForm,
  onContinue,
}: {
  form: any
  setForm: (v: any) => void
  onContinue: () => void
}) {
  const handleChange = (key: string, val: string) => {
    setForm({ ...form, [key]: val })
  }

  const isValid = form.firstName && form.lastName && form.address && form.city && form.zip && form.email && form.phone

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isValid) {
      onContinue()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <section>
        <h2 className="flex items-center gap-2 text-xl font-bold text-foreground">
          <MapPin className="h-5 w-5 text-primary" /> Delivery Address
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="First name" required value={form.firstName} onChange={(e) => handleChange('firstName', e.target.value)} placeholder="Alex" />
          <Field label="Last name" required value={form.lastName} onChange={(e) => handleChange('lastName', e.target.value)} placeholder="Mercer" />
          <div className="sm:col-span-2">
            <Field label="Address Line" required value={form.address} onChange={(e) => handleChange('address', e.target.value)} placeholder="123 Innovation Drive, Apt 4B" />
          </div>
          <Field label="City" required value={form.city} onChange={(e) => handleChange('city', e.target.value)} placeholder="Bengaluru" />
          <Field label="State" required value={form.state} onChange={(e) => handleChange('state', e.target.value)} placeholder="Karnataka" />
          <Field label="ZIP code / Postal" required value={form.zip} onChange={(e) => handleChange('zip', e.target.value)} placeholder="560001" />
          <Field label="Country" required value={form.country} onChange={(e) => handleChange('country', e.target.value)} placeholder="India" />
        </div>
      </section>

      <section className="border-t border-border pt-6">
        <h2 className="flex items-center gap-2 text-xl font-bold text-foreground">
          <Mail className="h-5 w-5 text-primary" /> Contact details
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="Email Address" required type="email" value={form.email} onChange={(e) => handleChange('email', e.target.value)} placeholder="alex@gmail.com" />
          <Field label="Contact Phone" required value={form.phone} onChange={(e) => handleChange('phone', e.target.value)} placeholder="+91 99999 88888" />
        </div>
      </section>

      <Button type="submit" variant="gradient" size="lg" className="px-8 py-5 rounded-xl uppercase font-semibold text-xs tracking-widest gap-1.5" disabled={!isValid}>
        Continue to Payment <ArrowRight className="h-4 w-4" />
      </Button>
    </form>
  )
}

/* Payment Step */
function StepPayment({
  cardNumber,
  setCardNumber,
  expiry,
  setExpiry,
  cvv,
  setCvv,
  cardName,
  setCardName,
  selectedMethod,
  setSelectedMethod,
  onBack,
  onReview,
}: any) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="flex items-center gap-2 text-xl font-bold text-foreground">
          <CreditCard className="h-5 w-5 text-primary" /> Secure Payment
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Transactions are encrypted and processed immediately.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <PaymentOption
          icon={<CreditCard className="h-5 w-5" />}
          label="Credit Card"
          active={selectedMethod === 'card'}
          onClick={() => setSelectedMethod('card')}
        />
        <PaymentOption
          icon={<Apple className="h-5 w-5" />}
          label="Apple Pay"
          active={selectedMethod === 'wallet'}
          onClick={() => setSelectedMethod('wallet')}
        />
        <PaymentOption
          icon={<Landmark className="h-5 w-5" />}
          label="Net Banking"
          active={selectedMethod === 'net_banking'}
          onClick={() => setSelectedMethod('net_banking')}
        />
      </div>

      {selectedMethod === 'card' && (
        <div className="rounded-3xl border border-border bg-card p-6 gap-4 flex flex-col shadow-sm">
          <div>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Card Number</Label>
            <Input
              value={cardNumber}
              onChange={(e) => setCardNumber(e.target.value)}
              className="mt-1.5 font-mono py-5 rounded-xl"
              placeholder="1234 1234 1234 1234"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Expiry Date</Label>
              <Input
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
                className="mt-1.5 font-mono py-5 rounded-xl"
                placeholder="MM / YY"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">CVV</Label>
              <Input
                value={cvv}
                onChange={(e) => setCvv(e.target.value)}
                type="password"
                className="mt-1.5 font-mono py-5 rounded-xl"
                placeholder="123"
              />
            </div>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Name on Card</Label>
            <Input
              value={cardName}
              onChange={(e) => setCardName(e.target.value)}
              className="mt-1.5 py-5 rounded-xl"
              placeholder="Alex Mercer"
            />
          </div>
        </div>
      )}

      <div className="flex gap-4 pt-4">
        <Button variant="secondary" size="lg" className="rounded-xl font-semibold uppercase text-xs tracking-widest gap-1.5 px-6" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Button variant="gradient" size="lg" className="flex-1 rounded-xl font-semibold uppercase text-xs tracking-widest gap-1.5" onClick={onReview}>
          Review Details <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

/* Review Step */
function StepReview({
  shippingForm,
  cardNumber,
  selectedMethod,
  cart,
  loading,
  onBack,
  onPlace,
}: any) {
  const summary = cart?.summary
  const items = cart?.items || []

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-foreground">Review Information</h2>

      <div className="space-y-3">
        <ReviewRow
          icon={<MapPin className="h-4 w-4" />}
          title="Shipping Details"
          body={`${shippingForm.firstName} ${shippingForm.lastName} · ${shippingForm.address}, ${shippingForm.city}, ${shippingForm.zip}`}
          onEdit={() => onBack()}
        />
        <ReviewRow
          icon={<CreditCard className="h-4 w-4" />}
          title="Payment Method"
          body={selectedMethod === 'card' ? `Card ending in ${cardNumber.slice(-4)}` : 'Digital Wallet / Netbanking'}
          onEdit={() => onBack()}
        />
        <ReviewRow
          icon={<Mail className="h-4 w-4" />}
          title="Contact Info"
          body={`${shippingForm.email} · ${shippingForm.phone}`}
          onEdit={() => onBack()}
        />
      </div>

      <div className="border-t border-border pt-6 mt-6">
        <h3 className="font-bold text-sm text-foreground uppercase tracking-wider mb-4">Cart List Summary</h3>
        <div className="space-y-3">
          {items.map((i: any) => (
            <div key={i.id} className="flex items-center gap-4 bg-card p-3 rounded-2xl border border-border shadow-sm">
              <img src={i.image_url || 'https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80'} alt={i.product_name} className="w-12 h-12 rounded-xl object-cover border" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold text-foreground">{i.product_name}</p>
                <p className="text-xs text-muted-foreground">Qty: {i.quantity}</p>
              </div>
              <span className="font-bold text-sm text-foreground">₹{i.total_price}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4 pt-4 border-t border-border">
        <Button variant="secondary" size="lg" className="rounded-xl font-semibold uppercase text-xs tracking-widest gap-1.5 px-6" onClick={onBack} disabled={loading}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Button variant="gradient" size="lg" className="flex-1 rounded-xl font-semibold uppercase text-xs tracking-widest gap-1.5 py-6" onClick={onPlace} disabled={loading}>
          <Lock className="h-4 w-4" /> {loading ? 'Processing Order...' : 'Confirm & Place Order'}
        </Button>
      </div>
    </div>
  )
}

/* Sidebar Order Summary */
function OrderSummary({
  cart,
  summary,
  step,
  updateItem,
  removeItem,
}: {
  cart: any
  summary: any
  step: number
  updateItem: (productId: string, qty: number) => Promise<any>
  removeItem: (productId: string, qty: number) => Promise<any>
}) {
  const items = cart?.items || []
  const [promoCode, setPromoCode] = useState('')
  const [discountAmount, setDiscountAmount] = useState(0)
  const [appliedCode, setAppliedCode] = useState('')
  const [promoLoading, setPromoLoading] = useState(false)

  const handleQtyChange = async (productId: string, currentQty: number, delta: number) => {
    const newQty = currentQty + delta
    if (newQty <= 0) {
      await removeItem(productId, currentQty)
    } else {
      await updateItem(productId, newQty)
    }
  }

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) return
    setPromoLoading(true)
    try {
      const { validateCouponApi } = await import('@/lib/api')
      const res = await validateCouponApi(promoCode, summary?.subtotal || 0)
      setDiscountAmount(res.discount_amount)
      setAppliedCode(res.code)
    } catch (err: any) {
      alert(err?.message || 'Invalid promo code')
    } finally {
      setPromoLoading(false)
    }
  }

  const finalTotal = Math.max(0, (summary?.total_amount || 0) - discountAmount)

  return (
    <aside className="glass border border-white/5 rounded-3xl p-6 shadow-sm flex flex-col gap-6">
      <h3 className="font-bold text-foreground text-sm uppercase tracking-wider border-b border-border pb-3">Order Summary</h3>

      <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
        {items.map((i: any) => (
          <div key={i.id} className="flex items-center gap-3">
            <img src={i.image_url || 'https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80'} alt={i.product_name} className="w-10 h-10 rounded-xl object-cover shrink-0 border" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-bold text-foreground">{i.product_name}</p>
              <p className="text-[10px] text-muted-foreground">₹{i.unit_price} each</p>
            </div>
            {step === 0 && (
              <div className="flex items-center bg-muted/40 p-0.5 rounded-lg border">
                <Button variant="ghost" size="icon-sm" className="h-6 w-6" onClick={() => handleQtyChange(i.product_id, i.quantity, -1)}>
                  <Minus className="h-3 w-3" />
                </Button>
                <span className="w-5 text-center font-mono text-xs font-semibold">{i.quantity}</span>
                <Button variant="ghost" size="icon-sm" className="h-6 w-6" onClick={() => handleQtyChange(i.product_id, i.quantity, 1)}>
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            )}
            {step > 0 && <span className="text-xs font-semibold text-muted-foreground px-2">x{i.quantity}</span>}
            <span className="text-right text-xs font-bold text-foreground w-14">₹{i.total_price}</span>
          </div>
        ))}
      </div>

      {/* Promo Code Box */}
      <div className="border-t border-border pt-4">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5 block">Promo Code</label>
        <div className="flex gap-2">
          <Input
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder="e.g. WELCOME50, SMART100"
            className="text-xs rounded-xl bg-card/60 uppercase font-mono"
          />
          <Button size="sm" variant="outline" className="rounded-xl text-xs px-3 shrink-0" onClick={handleApplyPromo} disabled={promoLoading}>
            Apply
          </Button>
        </div>
        
        {/* Quick Promo Chips */}
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {[
            { code: 'WELCOME50', label: '50% OFF' },
            { code: 'SMART100', label: '₹100 OFF' },
            { code: 'FREESHIP', label: 'Free Delivery' }
          ].map(c => (
            <button
              key={c.code}
              onClick={async () => {
                setPromoCode(c.code)
                setPromoLoading(true)
                try {
                  const { validateCouponApi } = await import('@/lib/api')
                  const res = await validateCouponApi(c.code, summary?.subtotal || 0)
                  setDiscountAmount(res.discount_amount)
                  setAppliedCode(res.code)
                } catch {
                  // fallback to optimistic
                  setDiscountAmount(c.code === 'WELCOME50' ? Math.round((summary?.subtotal || 0) * 0.5) : c.code === 'FREESHIP' ? 40 : 100)
                  setAppliedCode(c.code)
                } finally { setPromoLoading(false) }
              }}
              className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg border border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 transition disabled:opacity-50"
              disabled={promoLoading}
            >
              {c.code} ({c.label})
            </button>
          ))}
        </div>

        {appliedCode && (
          <div className="mt-2.5 flex items-center justify-between text-[11px] text-emerald-600 font-semibold bg-emerald-500/10 px-2.5 py-1.5 rounded-xl border border-emerald-500/20">
            <span>Promo applied: {appliedCode}</span>
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          </div>
        )}
      </div>

      <div className="border-t border-border pt-4 flex flex-col gap-2.5 text-xs">
        <SummaryRow label="Subtotal" value={`₹${summary?.subtotal || 0}`} />
        <SummaryRow label="Shipping" value="Free Delivery" />
        <SummaryRow label="Estimated Tax (18% GST)" value={`₹${summary?.tax || 0}`} />
        {discountAmount > 0 && (
          <div className="flex justify-between text-xs text-success font-semibold">
            <span>Promo Discount</span>
            <span>-₹{discountAmount}</span>
          </div>
        )}
        <div className="flex justify-between border-t border-border pt-3 text-sm font-black text-foreground">
          <span>Total</span>
          <span>₹{finalTotal.toFixed(2)}</span>
        </div>
      </div>

      <div className="rounded-xl bg-success/[0.06] p-3 text-[10px] text-success flex gap-2 items-center">
        <Store className="h-4 w-4 shrink-0" /> Verified checkout via SmartCart vision analytics.
      </div>
    </aside>
  )
}

/* Helper Components */
function Field({ label, className, ...props }: ComponentProps<typeof Input> & { label: string; className?: string }) {
  return (
    <div className={className}>
      <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">{label}</Label>
      <Input {...props} className="mt-1.5 bg-card/50 border border-border rounded-xl py-5 text-sm" />
    </div>
  )
}

function PaymentOption({ icon, label, active, onClick }: { icon: any; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center justify-center gap-2 rounded-xl border px-4 py-4 text-xs font-semibold transition uppercase tracking-wider',
        active ? 'border-primary bg-primary/5 text-primary' : 'border-border bg-card hover:bg-muted/30 text-muted-foreground',
      )}
    >
      {icon} {label}
    </button>
  )
}

function ReviewRow({ icon, title, body, onEdit }: { icon: any; title: string; body: string; onEdit: () => void }) {
  return (
    <div className="flex items-start gap-4 bg-card/60 border border-border p-4 rounded-2xl shadow-sm">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary shrink-0">
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold text-foreground">{title}</p>
        <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">{body}</p>
      </div>
      <Button variant="ghost" size="sm" className="rounded-lg text-xs" onClick={onEdit}>
        Change
      </Button>
    </div>
  )
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs text-muted-foreground">
      <span>{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
    </div>
  )
}

/* Success Confirmation Screen */
function OrderConfirmationScreen({ order, address }: { order: Order; address: any }) {
  const navigate = useNavigate()

  return (
    <div className="mx-auto max-w-xl px-6 py-20 text-center flex flex-col items-center justify-center gap-8 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-80 h-80 bg-primary/5 rounded-full blur-[100px] -z-10 mix-blend-multiply"></div>

      <div className="w-20 h-20 bg-success/10 text-success rounded-full flex items-center justify-center animate-bounce shadow-md">
        <Check className="h-10 w-10" />
      </div>

      <div className="space-y-2">
        <Badge variant="ai" className="gap-1.5 px-3 py-1">
          <Sparkles className="h-3.5 w-3.5 text-secondary" /> Receipt Logged
        </Badge>
        <h2 className="text-3xl font-sans font-extrabold text-foreground">Thank you for your order!</h2>
        <p className="text-xs text-muted-foreground">
          Order number <span className="font-mono font-bold text-foreground">{order.order_number}</span>
        </p>
      </div>

      <div className="w-full bg-card border border-border p-6 rounded-3xl text-left space-y-4 shadow-sm text-xs">
        <div className="border-b pb-3">
          <p className="font-bold text-foreground uppercase tracking-wider mb-1">Shipping Details</p>
          <p className="text-muted-foreground leading-relaxed">
            {address.firstName} {address.lastName} <br />
            {address.address}, {address.city}, {address.zip} <br />
            Phone: {address.phone}
          </p>
        </div>
        <div>
          <p className="font-bold text-foreground uppercase tracking-wider mb-2">Order Items</p>
          <ul className="space-y-2">
            {order.items?.map((i) => (
              <li key={i.id} className="flex justify-between items-center text-muted-foreground">
                <span className="truncate max-w-xs">{i.product_name} <span className="font-bold text-foreground">x{i.quantity}</span></span>
                <span className="font-bold text-foreground">₹{i.total_price}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="border-t pt-3 flex justify-between items-center text-sm font-black text-foreground">
          <span>Amount Paid</span>
          <span>₹{order.total_amount}</span>
        </div>
      </div>

      <div className="flex gap-4 w-full">
        <Button variant="secondary" className="flex-1 py-5 rounded-xl" onClick={() => navigate('/collections')}>
          Continue Shopping
        </Button>
        <Button variant="gradient" className="flex-1 py-5 rounded-xl uppercase font-semibold text-xs tracking-widest gap-2" onClick={() => navigate('/analytics')}>
          View Intelligence <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}