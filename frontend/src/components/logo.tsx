import { cn } from '@/lib/cn'

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-6 w-6', className)}
      aria-hidden="true"
    >
      <circle cx="9" cy="20" r="1.4" />
      <circle cx="17.5" cy="20" r="1.4" />
      <path d="M3 3h2l2.2 11.2a1.5 1.5 0 0 0 1.5 1.3h8.9a1.5 1.5 0 0 0 1.5-1.2L21 7H6.2" />
      <circle cx="18" cy="7.5" r="1" fill="currentColor" stroke="none" />
      <circle cx="18" cy="7.5" r="3.4" stroke="currentColor" strokeOpacity="0.4" />
    </svg>
  )
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <span className="relative grid h-9 w-9 place-items-center rounded-xl border border-primary/30 bg-primary/10 text-primary shadow-[0_0_18px_rgba(79,140,255,0.25)]">
        <LogoMark className="h-5 w-5" />
      </span>
      <span className="leading-none">
        <span className="block text-[15px] font-bold tracking-tight text-foreground">
          SmartCart<span className="text-gradient"> AI</span>
        </span>
        <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Neural Retail
        </span>
      </span>
    </span>
  )
}