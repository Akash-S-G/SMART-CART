import { Link, useLocation } from 'react-router-dom'
import { Logo } from '@/components/logo'

const COLUMNS = [
  {
    title: 'Platform',
    links: ['Vision API', 'Edge SDKs', 'Retail Analytics', 'Hardware Integration'],
  },
  {
    title: 'Company',
    links: ['About Us', 'Careers', 'Blog', 'Contact'],
  },
]

export function Footer() {
  const location = useLocation()
  if (location.pathname.startsWith('/checkout')) return null

  return (
    <footer className="border-t border-black/[0.06]">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr_1fr_1.4fr]">
          <div>
            <Link to="/">
              <Logo />
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Building the future of frictionless commerce through advanced computer vision and
              neural networks.
            </p>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
                {col.title}
              </h4>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((link) => (
                  <li key={link}>
                    <Link
                      to="/collections"
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div>
            <h4 className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-foreground">
              Stay Updated
            </h4>
            <p className="mt-4 text-sm text-muted-foreground">
              Subscribe to our newsletter for the latest AI retail insights.
            </p>
            <form
              className="mt-4 flex gap-2"
              onSubmit={(e) => e.preventDefault()}
            >
              <input
                type="email"
                placeholder="you@example.com"
                className="h-10 w-full min-w-0 flex-1 rounded-lg border border-input/80 bg-black/[0.03] px-3.5 text-sm placeholder:text-muted-foreground/60 focus:border-primary/70 focus:outline-none focus:ring-4 focus:ring-primary/15"
              />
              <button
                type="submit"
                className="h-10 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-90"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-black/[0.06] pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© 2026 SmartCart AI Inc. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/collections" className="transition-colors hover:text-foreground">
              Privacy Policy
            </Link>
            <Link to="/collections" className="transition-colors hover:text-foreground">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}