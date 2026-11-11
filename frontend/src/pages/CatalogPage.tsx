import { useState, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { api, type Product, type PagedProducts } from "../lib/api"

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [q, setQ] = useState("")
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined)
  const [limit, setLimit] = useState(20)
  const [offset, setOffset] = useState(0)

  const fetchProducts = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await api.listProducts({ category_id: categoryId, search: q || undefined, limit, offset })
      setProducts(data.items)
      setTotal(data.total)
    } catch (err: any) {
      setError(err.message || "Failed to load products")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [q, categoryId, limit, offset])

  const pageCount = Math.ceil(total / limit)

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row gap-4 justify-between items-end mb-6">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        </div>
        <div className="flex flex-col lg:flex-row gap-3 w-full lg:w-auto">
          <input
            type="text"
            placeholder="Search products"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full lg:w-auto px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
          />
          <select
            value={categoryId === undefined ? "" : String(categoryId)}
            onChange={(e) => setCategoryId(e.target.value === "" ? undefined : Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 outline-none"
          >
            <option value="">All categories</option>
            <option value="1">Electronics</option>
            <option value="2">Furniture</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">Loading products</div>
      ) : total === 0 ? (
        <p className="text-gray-500 text-center py-10">No products found.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
          <div className="mt-6 flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
              <span className="px-3 py-1.5 text-sm text-gray-600">
                Page {Math.floor(offset / limit) + 1} of {pageCount}
              </span>
            </div>
          </div>
        </>
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
        disabled={!inStock || added}
        className={inStock
          ? "w-full mt-3 py-2 rounded-md font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
          : "w-full mt-3 py-2 rounded-md font-medium bg-gray-200 text-gray-400"}
      >
        {added ? "Added" : "Add to cart"}
      </button>
      <Link to={`/products/${product.id}`} className="block text-center mt-2 text-sm text-indigo-600">
        View details
      </Link>
    </div>
  )
}
