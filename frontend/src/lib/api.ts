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
  return res
}

export async function listProductsApi(skip = 0, limit = 40): Promise<Product[]> {
  return getJson<Product[]>(`/products?skip=${skip}&limit=${limit}`)
}

export async function searchProductsApi(keyword: string): Promise<Product[]> {
  return getJson<Product[]>(`/products/search/?keyword=${encodeURIComponent(keyword)}`)
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

