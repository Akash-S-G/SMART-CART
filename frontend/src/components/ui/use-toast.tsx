import * as React from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { cva, type VariantProps } from 'class-variance-authority'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'

type ToasterToast = ToastPrimitive.ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  icon?: React.ReactNode
}

const ActionTypes = {
  ADD_TOAST: 'ADD_TOAST',
  UPDATE_TOAST: 'UPDATE_TOAST',
  DISMISS_TOAST: 'DISMISS_TOAST',
  REMOVE_TOAST: 'REMOVE_TOAST',
} as const

let count = 0
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = (typeof ActionTypes)[keyof typeof ActionTypes]

type Action =
  | { type: ActionType['ADD_TOAST']; toast: ToasterToast }
  | { type: ActionType['UPDATE_TOAST']; toast: Partial<ToasterToast> }
  | { type: ActionType['DISMISS_TOAST']; toastId?: ToasterToast['id'] }
  | { type: ActionType['REMOVE_TOAST']; toastId?: ToasterToast['id'] }

interface State {
  toasts: ToasterToast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()
const addToRemoveQueue = (toastId: string) => {
  if (toastTimeouts.has(toastId)) return
  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({ type: ActionTypes.REMOVE_TOAST, toastId })
  }, 5000)
  toastTimeouts.set(toastId, timeout)
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case ActionTypes.ADD_TOAST:
      return { ...state, toasts: [action.toast, ...state.toasts].slice(0, 3) }
    case ActionTypes.UPDATE_TOAST:
      return {
        ...state,
        toasts: state.toasts.map((t) => (t.id === action.toast.id ? { ...t, ...action.toast } : t)),
      }
    case ActionTypes.DISMISS_TOAST: {
      const { toastId } = action
      if (toastId) addToRemoveQueue(toastId)
      else state.toasts.forEach((t) => addToRemoveQueue(t.id))
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined ? { ...t, open: false } : t,
        ),
      }
    }
    case ActionTypes.REMOVE_TOAST:
      if (action.toastId === undefined) return { ...state, toasts: [] }
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.toastId) }
  }
}

let dispatch: React.Dispatch<Action> = () => {}

export interface Toast extends VariantProps<typeof toastVariants> {}
const toastVariants = cva('', { variants: {} })

const listeners: Array<(state: State) => void> = []
let memoryState: State = { toasts: [] }

function dispatchToReducer(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => listener(memoryState))
}

type ToastProps = { title?: React.ReactNode; description?: React.ReactNode; variant?: 'default' | 'success' | 'destructive' | 'ai'; icon?: React.ReactNode }

function toast(props: ToastProps) {
  const id = genId()
  update({ id, open: true, onOpenChange: (open) => { if (!open) dismiss(id) }, ...props } as Toast)
  addToRemoveQueue(id)
}

function update(props: ToasterToast) {
  dispatch({ type: ActionTypes.UPDATE_TOAST, toast: props })
}

function dismiss(toastId?: string) {
  dispatch({ type: ActionTypes.DISMISS_TOAST, toastId })
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)
  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) listeners.splice(index, 1)
    }
  }, [])
  return { ...state, toast, dismiss }
}

export { toast, useToast, dismiss }

/* ---- Presentational primitives re-exported ---- */
const ToastPrimitiveProvider = ToastPrimitive.Provider
const ToastPrimitiveViewport = ToastPrimitive.Viewport
const ToastPrimitiveTitle = ToastPrimitive.Title
const ToastPrimitiveDescription = ToastPrimitive.Description
const ToastPrimitiveAction = ToastPrimitive.Action
const ToastPrimitiveClose = ToastPrimitive.Close
const ToastPrimitiveRoot = ToastPrimitive.Root

export function ToastAction({ className, ...props }: React.ComponentProps<typeof ToastPrimitiveAction>) {
  return <ToastPrimitiveAction className={cn('inline-flex h-8 items-center justify-center rounded-md border border-border bg-muted px-3 text-sm font-medium transition-colors hover:bg-muted', className)} {...props} />
}

export function ToastClose({ className, ...props }: React.ComponentProps<typeof ToastPrimitiveClose>) {
  return <ToastPrimitiveClose className={cn('absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100', className)} toast-close="" {...props}><X className="h-4 w-4" /></ToastPrimitiveClose>
}

export function ToastTitle({ className, ...props }: React.ComponentProps<typeof ToastPrimitiveTitle>) {
  return <ToastPrimitiveTitle className={cn('text-sm font-semibold', className)} {...props} />
}

export function ToastDescription({ className, ...props }: React.ComponentProps<typeof ToastPrimitiveDescription>) {
  return <ToastPrimitiveDescription className={cn('text-sm text-muted-foreground opacity-90', className)} {...props} />
}