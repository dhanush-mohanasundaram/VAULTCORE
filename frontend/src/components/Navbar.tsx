import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { api, type User } from "../lib/api"

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null)
  const navigate = useNavigate()

  const raw = localStorage.getItem("token")
  if (raw && !user) {
    api.me().then(setUser).catch(() => localStorage.removeItem("token"))
  }

  const logout = () => {
    localStorage.removeItem("token")
    setUser(null)
    navigate("/login")
  }

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link to="/" className="font-bold text-xl tracking-tight text-gray-900">
            VAULTCORE
          </Link>
          <div className="hidden md:flex space-x-8">
            <Link to="/" className={navClass("/")}>Catalog</Link>
            <Link to="/cart" className={navClass("/cart")}>
              Cart
            </Link>
            <Link to="/orders" className={navClass("/orders")}>My Orders</Link>
            {user?.roles.includes("admin") && (
              <Link to="/admin" className={navClass("/admin")}>Admin</Link>
            )}
          </div>
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <span className="text-sm text-gray-600">{user.email}</span>
                <button onClick={logout} className="text-sm text-red-600 hover:text-red-800">
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900">
                  Sign in
                </Link>
                <Link to="/register" className="text-sm bg-gray-900 text-white px-3 py-1.5 rounded hover:bg-gray-800">
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

function navClass(path: string) {
  return `text-sm font-medium transition-colors ${location.pathname === path ? "text-indigo-600" : "text-gray-600 hover:text-gray-900"}`
}

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow border border-gray-200">{children}</div>
    </div>
  )
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      {subtitle && <p className="text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}

export function AdminOnly({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token")
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    if (!payload.roles?.includes("admin")) return null
  } catch {
    return null
  }
  return <>{children}</>
}
