import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api, type Order } from "../lib/api"

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    api.listOrders().then(setOrders).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [])

  const statusColor = (status: string) => {
    switch (status) {
      case "paid": return "text-green-600 bg-green-50"
      case "completed": return "text-indigo-600 bg-indigo-50"
      case "cancelled": return "text-red-600 bg-red-50"
      default: return "text-gray-600 bg-gray-50"
    }
  }

  if (loading) return <div className="text-center py-10">Loading orders…</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {orders.length === 0 ? (
        <p className="text-gray-500">No orders yet.</p>
      ) : (
        <table className="w-full border border-gray-200 rounded-lg overflow-hidden bg-white">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-sm font-medium text-gray-600">Order #</th>
              <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Total</th>
              <th className="px-4 py-3 text-sm font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 text-sm font-medium text-gray-600">Date</th>
              <th className="px-4 py-3 text-sm font-medium text-gray-600"></th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-b border-gray-100">
                <td className="px-4 py-3">#{o.id}</td>
                <td className="px-4 py-3 text-right font-medium">₹{o.total}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor(o.status)}`}>
                    {o.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{new Date(o.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <Link to={`/orders/${o.id}`} className="text-indigo-600 hover:text-indigo-500 text-sm">
                    Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
