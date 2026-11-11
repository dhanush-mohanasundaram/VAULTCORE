/// <reference types="vite/client" />
const API_BASE = import.meta.env.VITE_API_BASE || ""

export class ApiError extends Error {
  status: number
  code: string
  request_id?: string
  details?: unknown

  constructor(status: number, message: string, code?: string, request_id?: string, details?: unknown) {
    super(message)
    this.status = status
    this.code = code || `http_${status}`
    this.request_id = request_id
    this.details = details
    this.name = "ApiError"
  }
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path: string, opts: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...opts.headers },
  })
  return res
}

export type User = { id: number; email: string; full_name?: string; roles: string[] }
export type Product = {
  id: number; name: string; description?: string; price: string; sku?: string;
  category_id?: number; stock: number; is_active: boolean; category_name?: string; created_at: string
}
export type CartItem = { id: number; product_id: number; product_name: string; quantity: number; unit_price: string; subtotal: string }
export type OrderItem = { id: number; product_id: number; product_name: string; quantity: number; unit_price: string; subtotal: string }
export type Order = { id: number; status: string; total: string; created_at: string; items: OrderItem[] }
export type AdminOrder = { id: number; customer_email: string; status: string; total: string; created_at: string }
export type Stats = { total_customers: number; total_products: number; total_orders: number; pending_orders: number; completed_orders: number; low_stock_alerts: number }

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    let message = text || `Request failed (${res.status})`
    let code = `http_${res.status}`
    let request_id: string | undefined
    let details: unknown
    try {
      const parsed = JSON.parse(text)
      if (parsed.error) {
        message = parsed.error.message || message
        code = parsed.error.code || code
        request_id = parsed.error.request_id
        details = parsed.error.details
      } else {
        message = parsed.message || message
      }
    } catch {
      // non-JSON error body; use raw text
    }
    throw new ApiError(res.status, message, code, request_id, details)
  }
  return (await res.json()) as T
}

export const api = {
  login: (email: string, password: string) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }).then((r) => json<{ access_token: string }>(r)),
  register: (email: string, password: string, full_name?: string) =>
    request("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }).then((r) => json<User>(r)),
  me: () => request("/api/auth/me").then((r) => json<User>(r)),

  listProducts: (categoryId?: number) => {
    const qs = categoryId === undefined ? "" : `?category_id=${categoryId}`
    return request(`/api/products${qs}`).then((r) => json<Product[]>(r))
  },
  getProduct: (id: number) => request(`/api/products/${id}`).then((r) => json<Product>(r)),
  createProduct: (body: any) => request("/api/products", { method: "POST", body: JSON.stringify(body) }).then((r) => json<Product>(r)),
  updateProduct: (id: number, body: any) => request(`/api/products/${id}`, { method: "PATCH", body: JSON.stringify(body) }).then((r) => json<Product>(r)),
  deleteProduct: (id: number) => request(`/api/products/${id}`, { method: "DELETE" }).then((r) => (r.ok ? undefined : json<never>(r))),
  seed: () => request("/api/products/seed", { method: "POST" }).then((r) => json<{ seeded: boolean }>(r)),

  getCart: () => request("/api/cart").then((r) => json<{ items: CartItem[]; total: string }>(r)),
  addToCart: (productId: number, quantity: number) =>
    request("/api/cart", { method: "POST", body: JSON.stringify({ product_id: productId, quantity }) }).then((r) => json<{ items: CartItem[]; total: string }>(r)),
  updateCartItem: (productId: number, quantity: number) =>
    request(`/api/cart/${productId}`, { method: "PATCH", body: JSON.stringify({ quantity }) }).then((r) => json<{ items: CartItem[]; total: string }>(r)),
  removeFromCart: (productId: number) =>
    request(`/api/cart/${productId}`, { method: "DELETE" }).then((r) => json<{ items: CartItem[]; total: string }>(r)),
  clearCart: () => request("/api/cart", { method: "DELETE" }).then((r) => json<{ ok: boolean }>(r)),

  checkout: (idempotencyKey: string) =>
    request("/api/orders/checkout", { method: "POST", body: JSON.stringify({ idempotency_key: idempotencyKey }) }).then((r) => json<Order>(r)),
  listOrders: () => request("/api/orders/").then((r) => json<Order[]>(r)),
  getOrder: (id: number) => request(`/api/orders/${id}`).then((r) => json<Order>(r)),

  adminUsers: () => request("/api/admin/users").then((r) => json<User[]>(r)),
  adminProducts: () => request("/api/admin/products").then((r) => json<Product[]>(r)),
  adminOrders: () => request("/api/admin/orders").then((r) => json<AdminOrder[]>(r)),
  setOrderStatus: (id: number, status: string) =>
    request(`/api/admin/orders/${id}/status`, { method: "PATCH", body: JSON.stringify(status) }).then((r) => json<AdminOrder>(r)),
  adminStats: () => request("/api/admin/stats").then((r) => json<Stats>(r)),
  adminLowStock: () => request("/api/admin/low-stock").then((r) => json<Product[]>(r)),
}
