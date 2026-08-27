import { getJson, postJson, putJson, patchJson, deleteJson, http } from '@/lib/http'
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

export interface ProductQuery {
  skip?: number
  limit?: number
  category_id?: string
  min_price?: number
  max_price?: number
  sort?: string
  search?: string
}

export async function listProductsApi(skip = 0, limit = 40): Promise<Product[]> {
  const res = await getJson<Product[]>(`/products?skip=${skip}&limit=${limit}`)
  return Array.isArray(res) ? res : []
}

export async function fetchProductsPageApi(query: ProductQuery): Promise<Product[]> {
  const params = new URLSearchParams()
  params.set('skip', String(query.skip ?? 0))
  params.set('limit', String(query.limit ?? 24))
  if (query.category_id) params.set('category_id', query.category_id)
  if (typeof query.min_price === 'number') params.set('min_price', String(query.min_price))
  if (typeof query.max_price === 'number') params.set('max_price', String(query.max_price))
  if (query.sort) params.set('sort', query.sort)
  const res = await getJson<Product[]>(`/products?${params.toString()}`)
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

export async function updateProductApi(productId: string, body: any): Promise<Product> {
  return putJson<Product, any>(`/products/${productId}`, body)
}

export async function deleteProductApi(productId: string): Promise<void> {
  return deleteJson<void>(`/products/${productId}`)
}

export async function uploadProductImageApi(file: File): Promise<{ image_url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<{ image_url: string }>('/products/upload-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function bulkUploadProductsApi(file: File): Promise<{ created: number; failed: number; errors: string[] }> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<{ created: number; failed: number; errors: string[] }>(
    '/products/bulk',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return response.data
}

export async function generateBarcodeApi(existing?: string): Promise<{ barcode: string; image: string }> {
  const qs = existing ? `?existing=${encodeURIComponent(existing)}` : ''
  return getJson<{ barcode: string; image: string }>(`/products/generate-barcode${qs}`)
}

export async function getOrderSlipApi(orderId: string): Promise<void> {
  const response = await http.get(`/orders/${orderId}/slip`, { responseType: 'blob' })
  const blob = response.data as Blob
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `slip_${orderId}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

export async function listAdminOrdersApi(page = 1, pageSize = 20): Promise<any> {
  return getJson<any>(`/orders/admin?page=${page}&page_size=${pageSize}`)
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

export interface RecipeResponse {
  title: string
  prompt: string
  ingredients: string[]
  steps: string[]
  products: { id: string; name: string; brand: string | null; price: number; image: string | null; ingredient: string }[]
  source: string
}

export async function generateRecipeApi(prompt: string): Promise<RecipeResponse> {
  return postJson<RecipeResponse, { prompt: string }>(`/ai/recipe`, { prompt })
}
