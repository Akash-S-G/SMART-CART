import { cn } from '@/lib/cn'

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
      aria-hidden="true"
    >
      <circle cx="9" cy="20" r="1.5" fill="currentColor" />
      <circle cx="18" cy="20" r="1.5" fill="currentColor" />
      <path d="M3 3h2l2.2 11.2a1.5 1.5 0 0 0 1.5 1.3h8.9a1.5 1.5 0 0 0 1.5-1.2L21 7H6.2" />
    </svg>
  )
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
        <LogoMark className="h-5 w-5 text-white" />
      </span>
      <span className="leading-none">
        <span className="block text-[17px] font-extrabold tracking-tight text-foreground">
          Smart<span className="text-primary">Cart</span>
        </span>
        <span className="mt-0.5 block text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
          Instant Grocery & AI
        </span>
      </span>
    </span>
  )
}