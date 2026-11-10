import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { api, type Order } from "../lib/api"

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      api.getOrder(Number(id)).then(setOrder).finally(() => setLoading(false))
    }
  }, [id])

  if (loading) return <div className="text-center py-10">Loading order…</div>
  if (!order) return <div className="text-center py-10 text-gray-500">Order not found.</div>

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Link to="/orders" className="text-sm text-indigo-600 mb-4 inline-block">← Back to orders</Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Order #{order.id}</h1>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className="font-medium">{order.status}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Total</div>
            <div className="font-bold">₹{order.total}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Date</div>
            <div className="text-sm text-gray-500">{new Date(order.created_at).toLocaleString()}</div>
          </div>
          <div className="col-span-2">
            <div className="text-sm text-gray-500">Items</div>
            <table className="w-full mt-2 text-left">
              <thead>
                <tr>
                  <th className="pb-2 text-sm text-gray-500">Product</th>
                  <th className="pb-2 text-sm text-gray-500 text-right">Price</th>
                  <th className="pb-2 text-sm text-gray-500 text-center">Qty</th>
                  <th className="pb-2 text-sm text-gray-500 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {order.items.map((it) => (
                  <tr key={it.id} className="border-b border-gray-100">
                    <td className="py-2">{it.product_name}</td>
                    <td className="py-2 text-right">₹{it.unit_price}</td>
                    <td className="py-2 text-center">{it.quantity}</td>
                    <td className="py-2 text-right">₹{it.subtotal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
