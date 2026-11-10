import { useState, useEffect } from "react"
import { useParams, Link } from "react-router-dom"
import { api, type Product } from "../lib/api"

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [qty, setQty] = useState(1)
  const [error, setError] = useState("")
  const [added, setAdded] = useState(false)

  useEffect(() => {
    if (id) api.getProduct(Number(id)).then(setProduct).catch(() => setError("Product not found"))
  }, [id])

  const add = async () => {
    if (!product) return
    try {
      await api.addToCart(product.id, qty)
      setAdded(true)
      setTimeout(() => setAdded(false), 1500)
    } catch (err: any) {
      setError(err.message || "Could not add to cart")
    }
  }

  if (!product)
    return (
      <div className="max-w-3xl mx-auto px-4 py-10 text-center">
        <p className="text-gray-500">{error || "Loading…"}</p>
        <Link to="/" className="text-indigo-600">Back to catalog</Link>
      </div>
    )

  const inStock = product.stock > 0 && product.is_active

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Link to="/" className="text-sm text-indigo-600 mb-4 inline-block">← Back to catalog</Link>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-gray-100 rounded-lg h-64 flex items-center justify-center">
          <span className="text-gray-400 text-sm">{product.name}</span>
        </div>
        <div className="space-y-4">
          <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
          <p className="text-gray-500">{product.description || ""}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">₹{product.price}</span>
            <span className={inStock ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
              {inStock ? `In stock — ${product.stock} available` : "Out of stock"}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Quantity</label>
            <input
              type="number"
              min="1"
              max={inStock ? product.stock : 0}
              value={qty}
              onChange={(e) => setQty(Math.max(1, Number(e.target.value || 1)))}
              className="w-20 px-3 py-2 border border-gray-300 rounded-md outline-none"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={add}
            disabled={!inStock || added}
            className={`w-full py-3 rounded-md font-semibold ${
              inStock ? "bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40" : "bg-gray-200 text-gray-400"
            }`}
          >
            {added ? "Added ✓" : "Add to cart"}
          </button>
        </div>
      </div>
    </div>
  )
}
