import { useState } from "react"
import { Link } from "react-router-dom"
import { api, type Order } from "../lib/api"

export default function CheckoutPage() {
  const [key, setKey] = useState(`vc-${Date.now()}`)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState("")
  const [order, setOrder] = useState<Order | null>(null)
  const placeOrder = async () => {
    setProcessing(true)
    setError("")
    try {
      const o = await api.checkout(key)
      setOrder(o)
    } catch (err: any) {
      setError(err.message || "Checkout failed")
      setKey(`vc-${Date.now()}`)
    } finally {
      setProcessing(false)
    }
  }

  if (order) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10 text-center">
        <div className="mb-4 text-green-600 text-2xl">✓</div>
        <h1 className="text-2xl font-bold text-gray-900">Order placed</h1>
        <p className="text-gray-500 mt-2">Thank you for your purchase.</p>
        <div className="mt-6 p-4 bg-indigo-50 border border-indigo-100 rounded-lg text-left">
          <div className="text-sm font-medium text-gray-900">Order #{order.id}</div>
          <div className="text-sm text-gray-600">Total: ₹{order.total}</div>
          <div className="text-sm text-green-600 mt-1">Status: {order.status}</div>
        </div>
        <Link to="/orders" className="mt-6 inline-block text-indigo-600 hover:text-indigo-500 font-medium">
          View all orders
        </Link>
        <Link to="/" className="mt-4 inline-block text-indigo-600 hover:text-indigo-500">Continue shopping</Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>
      <p className="text-gray-600 mb-6">
        Simulated payment — no real money is processed. Submitting twice with the same key is safely ignored.
      </p>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">Idempotency key</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
              readOnly
            />
            <button
              onClick={() => setKey(`vc-${Date.now()}`)}
              className="px-3 py-2 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
            >
              New key
            </button>
          </div>
          <p className="text-xs text-gray-500">Duplicate requests with the same key return the same order.</p>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={placeOrder}
            disabled={processing}
            className="w-full py-3 bg-indigo-600 text-white rounded-md font-semibold disabled:opacity-60 hover:bg-indigo-700"
          >
            {processing ? "Placing order…" : "Place order"}
          </button>
        </div>
      </div>
      <Link to="/cart" className="mt-4 inline-block text-indigo-600 hover:text-indigo-500">← Back to cart</Link>
    </div>
  )
}
