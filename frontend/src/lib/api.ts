import { getJson, postJson, patchJson, deleteJson, http } from '@/lib/http'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  Product,
  Cart,
  Order,
  OrderListResponse,
  Payment,
  PaymentMethod,
  DetectionResult,
} from '@/types/api'

/* ==========================================================================
   AUTHENTICATION APIs
   ========================================================================== */

export async function loginApi(body: LoginRequest): Promise<TokenResponse> {
  return postJson<TokenResponse, LoginRequest>('/auth/login', body)
}

export async function registerApi(body: RegisterRequest): Promise<TokenResponse> {
  return postJson<TokenResponse, RegisterRequest>('/auth/register', body)
}

export async function googleLoginApi(body: {
  code?: string
  redirect_uri?: string
  fallback_url?: string
  id_token?: string
  email?: string
  username?: string
  first_name?: string
  last_name?: string
  profile_image?: string
}): Promise<TokenResponse> {
  return postJson<TokenResponse, any>('/auth/google-login', body)
}

export async function getProfileApi(): Promise<User> {
  return getJson<User>('/auth/me')
}

/* ==========================================================================
   CATALOG (PRODUCTS) APIs
   ========================================================================== */

export async function getCategoriesApi(): Promise<Category[]> {
  const res = await getJson<Category[]>('/products/categories')
  return Array.isArray(res) ? res : []
}

export async function listProductsApi(skip = 0, limit = 40): Promise<Product[]> {
  const res = await getJson<Product[]>(`/products?skip=${skip}&limit=${limit}`)
  return Array.isArray(res) ? res : []
}

export async function listAllProductsApi(): Promise<Product[]> {
  const pageSize = 500
  const all: Product[] = []
  let skip = 0
  while (true) {
    const batch = await listProductsApi(skip, pageSize)
    if (!batch.length) break
    all.push(...batch)
    if (batch.length < pageSize) break
    skip += pageSize
  }
  return all
}

export async function searchProductsApi(keyword: string): Promise<Product[]> {
  const res = await getJson<Product[]>(`/products/search/?keyword=${encodeURIComponent(keyword)}`)
  return Array.isArray(res) ? res : []
}

export async function getProductApi(id: string): Promise<Product> {
  return getJson<Product>(`/products/${id}`)
}

/* ==========================================================================
   CART APIs
   ========================================================================== */

export async function getCartApi(): Promise<Cart> {
  return getJson<Cart>('/cart')
}

export async function addToCartApi(productId: string, quantity = 1): Promise<Cart> {
  return postJson<Cart, { product_id: string; quantity: number }>('/cart/items', {
    product_id: productId,
    quantity,
  })
}

export async function updateCartItemApi(productId: string, quantity: number): Promise<Cart> {
  return patchJson<Cart, { quantity: number }>(`/cart/items/${productId}`, {
    quantity,
  })
}

export async function removeCartItemApi(productId: string): Promise<Cart> {
  return deleteJson<Cart>(`/cart/items/${productId}`)
}

export async function clearCartApi(): Promise<{ message: string }> {
  return deleteJson<{ message: string }>('/cart')
}

/* ==========================================================================
   ORDERS APIs
   ========================================================================== */

export async function checkoutApi(): Promise<{ order: Order }> {
  return postJson<{ order: Order }>('/orders/checkout')
}

export async function listOrdersApi(page = 1, pageSize = 20): Promise<OrderListResponse> {
  return getJson<OrderListResponse>(`/orders?page=${page}&page_size=${pageSize}`)
}

export async function getOrderApi(orderId: string): Promise<Order> {
  return getJson<Order>(`/orders/${orderId}`)
}

/* ==========================================================================
   PAYMENT APIs
   ========================================================================== */

export async function createPaymentApi(orderId: string, method: PaymentMethod): Promise<Payment> {
  return postJson<Payment, { order_id: string; payment_method: PaymentMethod }>('/payments', {
    order_id: orderId,
    payment_method: method,
  })
}

export async function verifyPaymentApi(transactionId: string): Promise<Payment> {
  return postJson<Payment, { transaction_id: string }>('/payments/verify', {
    transaction_id: transactionId,
  })
}

/* ==========================================================================
   AI SCANNER APIs
   ========================================================================== */

export async function detectImageApi(file: File): Promise<DetectionResult> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<DetectionResult>('/ai/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function detectAndAddApi(file: File): Promise<DetectionResult> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<DetectionResult>('/ai/detect-and-add', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function createProductApi(body: any): Promise<Product> {
  return postJson<Product, any>('/products', body)
}

/* ==========================================================================
   REVIEWS APIs
   ========================================================================== */

export interface Review {
  id: string
  product_id: string
  user_name: string | null
  rating: number
  title: string | null
  body: string
  verified_purchase: boolean
  helpful_count: number
  review_date: string
  is_generated: boolean
}

export async function getProductReviewsApi(productId: string, page = 1): Promise<Review[]> {
  const res = await getJson<Review[]>(`/products/${productId}/reviews?page=${page}&page_size=10`)
  return Array.isArray(res) ? res : []
}

export async function createReviewApi(
  productId: string,
  body: { rating: number; title?: string; body: string }
): Promise<Review> {
  return postJson<Review, typeof body>(`/products/${productId}/reviews`, body)
}

export async function markReviewHelpfulApi(productId: string, reviewId: string): Promise<Review> {
  return postJson<Review, Record<string, never>>(`/products/${productId}/reviews/${reviewId}/helpful`, {})
}

/* ==========================================================================
   ORDER MANAGEMENT APIs
   ========================================================================== */

export async function cancelOrderApi(orderId: string): Promise<{ message: string }> {
  return patchJson<{ message: string }, Record<string, never>>(`/orders/${orderId}/cancel`, {})
}

/* ==========================================================================
   WISHLIST & COUPON & ANALYTICS APIs
   ========================================================================== */

export async function getWishlistApi(): Promise<Product[]> {
  const res = await getJson<Product[]>('/wishlist')
  return Array.isArray(res) ? res : []
}

export async function addWishlistApi(productId: string): Promise<any> {
  return postJson<any, Record<string, never>>(`/wishlist/${productId}`, {})
}

export async function removeWishlistApi(productId: string): Promise<any> {
  return deleteJson<any>(`/wishlist/${productId}`)
}

export async function validateCouponApi(code: string, orderAmount: number): Promise<any> {
  return postJson<any, any>('/coupons/validate', { code, order_amount: orderAmount })
}

export async function getDashboardAnalyticsApi(): Promise<any> {
  return getJson<any>('/analytics/dashboard')
}

export async function getRealCustomersApi(): Promise<any[]> {
  return getJson<any[]>('/analytics/customers')
}

export async function getRealLogsApi(): Promise<any[]> {
  return getJson<any[]>('/analytics/logs')
}

export async function restockProductApi(productId: string, quantity: number): Promise<Product> {
  return postJson<Product, { quantity: number }>(`/products/${productId}/restock`, { quantity })
}
