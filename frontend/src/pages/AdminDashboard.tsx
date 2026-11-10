import { useEffect, useState } from "react"
import { api, type Stats, type AdminOrder, type Product } from "../lib/api"
import { AdminOnly } from "../components/Navbar"

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats>({
    total_customers: 0, total_products: 0, total_orders: 0, pending_orders: 0, completed_orders: 0, low_stock_alerts: 0,
  })
  const [lowStock, setLowStock] = useState<Product[]>([])
  const [recentOrders, setRecentOrders] = useState<AdminOrder[]>([])

  useEffect(() => {
    Promise.all([api.adminStats(), api.adminLowStock(), api.adminOrders()]).then(
      ([s, ls, orders]) => {
        setStats(s)
        setLowStock(ls)
        setRecentOrders(orders.slice(0, 5))
      },
    ).finally(() => {})
  }, [])

  return (
    <AdminOnly>
      <div className="max-w-7xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <StatCard title="Total Customers" value={stats.total_customers} />
          <StatCard title="Total Products" value={stats.total_products} />
          <StatCard title="Total Orders" value={stats.total_orders} />
          <StatCard title="Pending Orders" value={stats.pending_orders} />
          <StatCard title="Completed Orders" value={stats.completed_orders} />
          <StatCard title="Low Stock Alerts" value={stats.low_stock_alerts} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="font-bold text-gray-900 mb-4">Low Stock Products</h2>
            {lowStock.length === 0 ? (
              <p className="text-gray-500 text-sm">All products are well stocked.</p>
            ) : (
              <ul className="space-y-3">
                {lowStock.map((p) => (
                  <li key={p.id} className="flex justify-between items-center p-2 border rounded bg-gray-50">
                    <span className="text-sm">{p.name}</span>
                    <span className="text-sm font-bold text-red-600">{p.stock} left</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="font-bold text-gray-900 mb-4">Recent Orders</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-2 text-left text-gray-500">Order</th>
                    <th className="pb-2 text-left text-gray-500">Customer</th>
                    <th className="pb-2 text-right text-gray-500">Total</th>
                    <th className="pb-2 text-left text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentOrders.map((o) => (
                    <tr key={o.id} className="border-b border-gray-100">
                      <td className="py-2">#{o.id}</td>
                      <td className="py-2 text-gray-700">{o.customer_email}</td>
                      <td className="py-2 text-right font-medium">₹{o.total}</td>
                      <td className="py-2">{o.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </AdminOnly>
  )
}

function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <p className="text-sm text-gray-500">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${value === 0 ? "text-gray-400" : "text-indigo-600"}`}>{value}</p>
    </div>
  )
}
