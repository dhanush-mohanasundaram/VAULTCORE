import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { api, type AdminOrder } from "../lib/api"

export default function AdminOrderEdit() {
  const { id } = useParams<{ id: string }>()
  const [order, setOrder] = useState<AdminOrder | null>(null)
  const [status, setStatus] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (id) {
      api.adminOrders().then((list) => {
        const o = list.find((x) => x.id === Number(id))
        setOrder(o ?? null)
        setStatus(o?.status ?? "")
      }).catch((err) => setError(err.message))
    }
  }, [id])

  if (!order) return <div className="max-w-xl mx-auto px-4 py-10 text-center">Loading order…</div>

  return (
    <div className="max-w-xl mx-auto px-4 py-6">
      <Link to="/admin/orders" className="text-sm text-indigo-600 mb-4 inline-block">← Back</Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Order #{order.id}</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-500">Customer</label>
            <p className="font-medium">{order.customer_email}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500">Total</label>
            <p className="font-medium">₹{order.total}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              {["pending", "paid", "completed", "cancelled"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => {
              setSaving(true)
              api.setOrderStatus(order.id, status).then(() => setSaving(false)).catch((err) => { setError(err.message); setSaving(false) })
            }}
            disabled={saving}
            className="w-full py-2 bg-indigo-600 text-white rounded-md font-medium disabled:opacity-60 hover:bg-indigo-700"
          >
            {saving ? "Saving…" : "Update status"}
          </button>
        </div>
      </div>
    </div>
  )
}
