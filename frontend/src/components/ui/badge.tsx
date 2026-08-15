import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-colors',
  {
    variants: {
      variant: {
        default: 'border-primary/20 bg-primary/10 text-primary',
        secondary: 'border-border bg-muted text-foreground',
        outline: 'border-border bg-background text-muted-foreground',
        success: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
        warning: 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400',
        destructive: 'border-destructive/20 bg-destructive/10 text-destructive',
        violet: 'border-violet-500/20 bg-violet-500/10 text-violet-600 dark:text-violet-400',
        ai: 'border-primary/20 bg-primary/10 text-primary',
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