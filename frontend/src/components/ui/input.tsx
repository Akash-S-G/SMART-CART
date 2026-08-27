import * as React from 'react'
import { cn } from '@/lib/cn'

export function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      className={cn(
        'flex h-10 w-full rounded-lg border border-input/80 bg-muted/40 px-3.5 py-2 text-sm text-foreground transition-colors placeholder:text-muted-foreground/60 focus-visible:border-primary/70 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}