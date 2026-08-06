import type { User, TokenResponse } from '@/lib/session'

export type { User, TokenResponse }

export type Role = User['role']

/* ---------------- Auth ---------------- */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}
export interface LoginRequest {
  email: string
  password: string
}
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}
export interface MessageResponse {
  message: string
}
export interface UpdateProfileRequest {
  username?: string
}

/* ---------------- Products ---------------- */
export interface Product {
  id: string
  sku: string
  barcode?: string | null
  name: string
  description?: string | null
  brand?: string | null
  category_id: string
  category_name?: string
  is_active: boolean
  price?: number
  compare_at_price?: number | null
  stock?: number
  rating?: number
  review_count?: number
  images?: string[]
  tags?: string[]
  created_at?: string
  updated_at?: string
}

export interface ProductCreate {
  name: string
  sku: string
  barcode?: string | null
  description?: string | null
  brand?: string | null
  category_id: string
  initial_stock: number
}
export interface ProductUpdate {
  name?: string | null
  description?: string | null
  brand?: string | null
  category_id?: string | null
}

export interface Category {
  id: string
  name: string
  slug: string
  image?: string
  icon?: string
  description?: string
  product_count?: number
  gradient?: string
}

/* ---------------- Cart ---------------- */
export interface CartItem {
  id: string
  product_id: string
  product_name: string
  sku: string
  image_url?: string | null
  quantity: number
  unit_price: number
  total_price: number
  available_stock: number
}
export interface CartSummary {
  subtotal: number
  discount: number
  tax: number
  total_amount: number
  total_items: number
  total_quantity: number
}
export interface Cart {
  id: string
  user_id: string
  status: string
  created_at?: string
  updated_at?: string
  items: CartItem[]
  summary: CartSummary
}

/* ---------------- Orders ---------------- */
export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'paid'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'cancelled'
  | 'refunded'

export interface OrderItem {
  id: string
  product_id: string
  product_name: string
  sku: string
  quantity: number
  unit_price: number
  total_price: number
  image_url?: string | null
}
export interface Order {
  id: string
  order_number: string
  status: OrderStatus
  subtotal: number
  discount: number
  tax: number
  total_amount: number
  created_at?: string
  items: OrderItem[]
  items_count?: number
  address?: Address
  payment?: PaymentSummary
  estimated_delivery?: string
}
export interface OrderListResponse {
  items: Order[]
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

/* ---------------- Payments ---------------- */
export type PaymentMethod =
  | 'cash'
  | 'card'
  | 'upi'
  | 'wallet'
  | 'net_banking'
  | 'razorpay'
  | 'stripe'

export type PaymentStatus =
  | 'pending'
  | 'processing'
  | 'paid'
  | 'failed'
  | 'cancelled'
  | 'refunded'

export interface PaymentSummary {
  id: string
  order_id?: string
  transaction_id: string
  amount: number
  status: PaymentStatus
  payment_method?: PaymentMethod
  created_at?: string
}
export interface Payment {
  id: string
  order_id: string
  user_id: string
  transaction_id: string
  gateway_reference?: string | null
  payment_method: PaymentMethod
  status: PaymentStatus
  currency: string
  amount: number
  created_at?: string
}

/* ---------------- AI ---------------- */
export interface DetectionBox {
  label: string
  confidence: number
  x: number
  y: number
  width: number
  height: number
}
export interface DetectionResult {
  request_id: string
  object_type: string
  confidence: number
  bbox?: DetectionBox
  matched_product?: Product | null
  latency_ms?: number
  model?: string
  image_url?: string
}
export interface DetectionLog {
  id: string
  request_id: string
  object_type: string
  confidence: number
  status: 'matched' | 'unmatched' | 'error'
  lat?: number
  lng?: number
  product_id?: string | null
  latency_ms?: number
  created_at?: string
}

/* ---------------- Address / Profile ---------------- */
export interface Address {
  id?: string
  label: string
  name: string
  phone: string
  line1: string
  line2?: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default?: boolean
  type?: 'home' | 'work' | 'other'
}

export interface SavedCard {
  id: string
  brand: string
  last4: string
  expiry: string
  name: string
  is_default?: boolean
}

/* ---------------- Notifications ---------------- */
export interface AppNotification {
  id: string
  type: 'order' | 'promo' | 'price' | 'ai' | 'system'
  title: string
  message: string
  read: boolean
  created_at?: string
}

/* ---------------- Admin ---------------- */
export interface InventoryRow {
  id: string
  sku: string
  name: string
  category: string
  stock: number
  reserved: number
  reorder_level: number
  status: 'in_stock' | 'low' | 'critical' | 'out'
  updated_at?: string
}

export interface Customer {
  id: string
  name: string
  email: string
  orders: number
  spent: number
  status: 'active' | 'dormant' | 'new' | 'vip'
  joined?: string
}

export interface ActivityEvent {
  id: string
  type: string
  user: string
  action: string
  resource: string
  detail: string
  ip?: string
  severity: 'info' | 'warning' | 'critical'
  created_at?: string
}

export interface InventoryTransaction {
  id: string
  product_id: string
  product_name: string
  change: number
  type: 'inbound' | 'outbound' | 'adjustment'
  reason: string
  user?: string
  created_at?: string
}