import { Link, useLocation } from 'react-router-dom'
import { Logo } from '@/components/logo'
import { ShieldCheck, Truck, Clock, RefreshCw } from 'lucide-react'

const COLUMNS = [
  {
    title: 'Categories',
    links: [
      { name: 'Dairy, Bread & Eggs', path: '/collections?category=Dairy' },
      { name: 'Atta, Rice & Dal', path: '/collections?category=Staples' },
      { name: 'Snacks & Munchies', path: '/collections?category=Snacks' },
      { name: 'Cold Drinks & Juices', path: '/collections?category=Beverages' },
      { name: 'Fresh Fruits & Veggies', path: '/collections?category=Produce' },
    ],
  },
  {
    title: 'Smart Features',
    links: [
      { name: 'AI Vision Camera Scanner', path: '/scanner' },
      { name: 'Instant Automated Cart', path: '/checkout' },
      { name: 'Live Driver Simulation', path: '/orders' },
      { name: 'Store Analytics Dashboard', path: '/analytics' },
    ],
  },
  {
    title: 'Customer Service',
    links: [
      { name: 'My Profile & Address', path: '/profile' },
      { name: 'Order History & Receipts', path: '/orders' },
      { name: 'Instant Refunds & Help', path: '/profile' },
      { name: 'Terms & Conditions', path: '/collections' },
    ],
  },
]

export function Footer() {
  const location = useLocation()
  if (location.pathname.startsWith('/checkout')) return null

  return (
    <footer className="border-t border-border bg-card/60">
      {/* Service Highlights Bar */}
      <div className="border-b border-border bg-muted/30 py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h5 className="text-xs font-bold text-foreground">10-Minute Delivery</h5>
              <p className="text-[11px] text-muted-foreground">Express store fulfillment</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h5 className="text-xs font-bold text-foreground">100% Fresh & Genuine</h5>
              <p className="text-[11px] text-muted-foreground">Direct from trusted suppliers</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <Truck className="h-5 w-5" />
            </div>
            <div>
              <h5 className="text-xs font-bold text-foreground">Free Delivery</h5>
              <p className="text-[11px] text-muted-foreground">On orders over ₹299</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <RefreshCw className="h-5 w-5" />
            </div>
            <div>
              <h5 className="text-xs font-bold text-foreground">Easy Returns</h5>
              <p className="text-[11px] text-muted-foreground">Instant refund upon report</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Link to="/">
              <Logo />
            </Link>
            <p className="mt-4 max-w-xs text-xs leading-relaxed text-muted-foreground">
              India's fastest AI-powered grocery shopping platform. Scan items directly with your camera or get instant 10-minute doorstep delivery.
            </p>
            <div className="mt-4 flex items-center gap-2 text-[11px] text-muted-foreground font-semibold">
              <span>Accepted Payments:</span>
              <span className="px-2 py-0.5 bg-muted rounded border border-border">UPI</span>
              <span className="px-2 py-0.5 bg-muted rounded border border-border">GPay</span>
              <span className="px-2 py-0.5 bg-muted rounded border border-border">Cards</span>
              <span className="px-2 py-0.5 bg-muted rounded border border-border">COD</span>
            </div>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
                {col.title}
              </h4>
              <ul className="mt-4 space-y-2">
                {col.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.path}
                      className="text-xs text-muted-foreground transition-colors hover:text-primary"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© 2026 SmartCart AI. All rights reserved. Express Grocery & AI Vision Platform.</p>
          <div className="flex gap-6 text-xs font-medium">
            <Link to="/collections" className="hover:text-primary">Privacy Policy</Link>
            <Link to="/collections" className="hover:text-primary">Terms of Service</Link>
            <Link to="/analytics" className="hover:text-primary">Store Health</Link>
          </div>
        </div>
      </div>
    </footer>
  )
}