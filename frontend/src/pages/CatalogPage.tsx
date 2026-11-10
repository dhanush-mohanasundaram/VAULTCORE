import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { api, type Product } from "../lib/api"

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState("")

  useEffect(() => {
    api.listProducts().then(setProducts).finally(() => setLoading(false))
  }, [])

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(q.toLowerCase()),
  )

  if (loading) return <div className="text-center py-10">Loading products…</div>

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex justify-between items-end mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <input
          type="text"
          placeholder="Search products…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-64 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>
      {filtered.length === 0 ? (
        <p className="text-gray-500">No products found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  )
}

function ProductCard({ product }: { product: Product }) {
  const [added, setAdded] = useState(false)
  const inStock = product.stock > 0 && product.is_active

  const add = async () => {
    try {
      await api.addToCart(product.id, 1)
      setAdded(true)
      setTimeout(() => setAdded(false), 1500)
    } catch (err: any) {
      alert(err.message || "Could not add to cart")
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition">
      <div className="flex-1 bg-gray-100 rounded-lg flex items-center justify-center h-32 mb-3">
        <span className="text-gray-400 text-sm">{product.name}</span>
      </div>
      <h3 className="font-semibold text-gray-900">{product.name}</h3>
      <p className="text-sm text-gray-500 line-clamp-2">{product.description || ""}</p>
      <div className="mt-2 flex justify-between items-baseline">
        <span className="font-bold text-lg">₹{product.price}</span>
        <span className={`${inStock ? "text-green-600" : "text-red-600"} text-xs font-medium`}>
          {inStock ? `In stock (${product.stock})` : "Out of stock"}
        </span>
      </div>
      <button
        onClick={add}
        disabled={!inStock}
        className={`w-full mt-3 py-2 rounded-md font-medium ${
          inStock
            ? "bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
            : "bg-gray-200 text-gray-400"
        }`}
      >
        {added ? "Added ✓" : "Add to cart"}
      </button>
      <Link to={`/products/${product.id}`} className="block text-center mt-2 text-sm text-indigo-600 hover:text-indigo-500">
        View details
      </Link>
    </div>
  )
}
