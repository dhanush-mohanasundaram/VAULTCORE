import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api, type Product } from "../lib/api"

export default function AdminProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.adminProducts({ limit: 100 }).then(setProducts).finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex justify-between items-end mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Product Management</h1>
        <Link to="/admin/products/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm">Add product</Link>
      </div>
      {loading ? <div className="text-center py-10">Loading…</div> : products.length === 0 ? (
        <p className="text-gray-500">No products.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border border-gray-200 rounded-lg overflow-hidden bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">SKU</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right">Price</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-center">Stock</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600">Category</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-center">Active</th>
                <th className="px-4 py-3 text-sm font-medium text-gray-600 text-right"></th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{p.sku || "—"}</td>
                  <td className="px-4 py-3 text-right">₹{p.price}</td>
                  <td className="px-4 py-3 text-center">{p.stock}</td>
                  <td className="px-4 py-3">{p.category_name || "—"}</td>
                  <td className="px-4 py-3 text-center">
                    {p.is_active ? <span className="text-green-600 text-xs font-medium">Active</span> : <span className="text-gray-400 text-xs">Inactive</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/admin/products/${p.id}`} className="text-indigo-600 hover:text-indigo-500 text-sm">Edit</Link>
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
