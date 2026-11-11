import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { api, type ProductInput } from "../lib/api"

export default function AdminProductForm() {
  const navigate = useNavigate()
  const [product, setProduct] = useState<ProductInput>({
    name: "", description: "", price: "", sku: "", stock: 0, is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await api.createProduct(product)
      navigate("/admin/products")
    } catch (err: any) {
      setError(err.message || "Save failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <Link to="/admin/products" className="text-sm text-indigo-600 mb-4 inline-block">← Back</Link>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Add Product</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      <form onSubmit={save} className="space-y-4 bg-white p-6 rounded-lg border border-gray-200">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Name</label>
          <input required value={product.name} onChange={(e) => setProduct({ ...product, name: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none" />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea value={product.description} onChange={(e) => setProduct({ ...product, description: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none" rows={3} />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Price (₹)</label>
          <input type="number" required value={product.price} onChange={(e) => setProduct({ ...product, price: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none" />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">SKU</label>
          <input value={product.sku} onChange={(e) => setProduct({ ...product, sku: e.target.value })} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none" />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Stock</label>
          <input type="number" min="0" required value={product.stock} onChange={(e) => setProduct({ ...product, stock: Number(e.target.value || 0) })} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none" />
        </div>
        <div className="flex items-center gap-3">
          <input type="checkbox" checked={product.is_active} onChange={(e) => setProduct({ ...product, is_active: e.target.checked })} />
          <label className="text-sm text-gray-700">Active</label>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={loading} className="w-full py-3 bg-indigo-600 text-white rounded-md font-semibold disabled:opacity-60 hover:bg-indigo-700">
          Create product
        </button>
      </form>
    </div>
  )
}
