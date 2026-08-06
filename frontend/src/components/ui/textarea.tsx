import * as React from 'react'
import { cn } from '@/lib/cn'

export function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      className={cn(
        'flex min-h-[90px] w-full rounded-lg border border-input/80 bg-black/[0.03] px-3.5 py-2.5 text-sm text-foreground transition-colors placeholder:text-muted-foreground/60 focus-visible:border-primary/70 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}