import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.08em] font-mono transition-colors',
  {
    variants: {
      variant: {
        default: 'border-primary/30 bg-primary/10 text-primary',
        secondary: 'border-secondary/30 bg-secondary/10 text-secondary',
        outline: 'border-black/10 bg-transparent text-muted-foreground',
        success: 'border-success/30 bg-success/10 text-success',
        warning: 'border-warning/30 bg-warning/10 text-warning',
        destructive: 'border-destructive/30 bg-destructive/10 text-destructive',
        violet: 'border-violet-500/30 bg-violet-500/10 text-violet-300',
        ai: 'border-secondary/40 bg-secondary/15 text-secondary shadow-[0_0_12px_rgba(103,232,249,0.15)]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  success?: boolean
  warning?: boolean
  destructive?: boolean
  ai?: boolean
}

export function Badge({ className, variant, success, warning, destructive, ai, ...props }: BadgeProps) {
  let resolvedVariant = variant
  if (!resolvedVariant) {
    if (success) resolvedVariant = 'success'
    else if (warning) resolvedVariant = 'warning'
    else if (destructive) resolvedVariant = 'destructive'
    else if (ai) resolvedVariant = 'ai'
  }
  return <div className={cn(badgeVariants({ variant: resolvedVariant }), className)} {...props} />
}

export { badgeVariants }