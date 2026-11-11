import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api, type AdminOrder } from "../lib/api"

export default function AdminOrders() {
  const [orders, setOrders] = useState<AdminOrder[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.adminOrders({ limit: 50 }).then(setOrders).finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <Link to="/admin" className="text-sm text-indigo-600 mb-4 inline-block">← Back to dashboard</Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Order Management</h1>
      {loading ? <div className="text-center py-10">Loading…</div> : orders.length === 0 ? (
        <p className="text-gray-500">No orders.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border border-gray-200 rounded-lg overflow-hidden bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">Order</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">Customer</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Total</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-gray-100">
                  <td className="px-4 py-3">#{o.id}</td>
                  <td className="px-4 py-3 text-gray-700">{o.customer_email}</td>
                  <td className="px-4 py-3 text-right font-medium">₹{o.total}</td>
                  <td className="px-4 py-3">{o.status}</td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/admin/orders/${o.id}`} className="text-indigo-600 hover:text-indigo-500 text-sm">Edit</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
