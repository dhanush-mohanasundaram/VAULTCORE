import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { api, type CartItem } from "../lib/api"

export default function CartPage() {
  const [cart, setCart] = useState<{ items: CartItem[]; total: string }>({ items: [], total: "0.00" })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const navigate = useNavigate()

  useEffect(() => {
    loadCart()
  }, [])

  const loadCart = () => {
    api.getCart().then(setCart).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }

  const updateQty = (productId: number, qty: number) => {
    if (qty < 0) return
    api.updateCartItem(productId, qty).then(setCart).catch((err) => setError(err.message))
  }

  const remove = (productId: number) => {
    api.removeFromCart(productId).then(setCart).catch((err) => setError(err.message))
  }

  const checkout = async () => {
    const key = `vc-${Date.now()}-${Math.random().toString(36).slice(2)}`
    try {
      const order = await api.checkout(key)
      navigate(`/orders/${order.id}`)
    } catch (err: any) {
      setError(err.message || "Checkout failed")
    }
  }

  if (loading) return <div className="text-center py-10">Loading cart…</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Shopping Cart</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {cart.items.length === 0 ? (
        <div className="text-center py-10 bg-white border border-gray-200 rounded-lg">
          <p className="text-gray-500">Your cart is empty.</p>
          <Link to="/" className="mt-4 inline-block text-indigo-600 hover:text-indigo-500">Browse products</Link>
        </div>
      ) : (
        <>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-left border-b border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-sm font-medium text-gray-600">Product</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Price</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-600 text-center">Qty</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Subtotal</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-600"></th>
                </tr>
              </thead>
              <tbody>
                {cart.items.map((item) => (
                  <tr key={item.id} className="border-b border-gray-100">
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.product_name}</div>
                    </td>
                    <td className="px-4 py-3 text-right">₹{item.unit_price}</td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        value={item.quantity}
                        onChange={(e) => updateQty(item.product_id, Number(e.target.value || 0))}
                        className="w-16 px-2 py-1 border border-gray-300 rounded-md text-center outline-none"
                      />
                    </td>
                    <td className="px-4 py-3 text-right">₹{item.subtotal}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => remove(item.product_id)}
                        className="text-sm text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="p-4 border-t border-gray-200 flex justify-between items-center">
              <div className="text-right">
                <div className="text-gray-600">Total</div>
                <div className="text-lg font-bold">₹{cart.total}</div>
              </div>
              <button
                onClick={checkout}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700"
              >
                Proceed to checkout
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
