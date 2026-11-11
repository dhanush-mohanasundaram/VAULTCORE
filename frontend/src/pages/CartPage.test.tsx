import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import CartPage from "./CartPage"
import * as api from "../lib/api"

vi.mock("../lib/api", () => ({
  api: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    updateCartItem: vi.fn(),
    removeFromCart: vi.fn(),
    checkout: vi.fn(),
    clearCart: vi.fn(),
  },
}))

describe("CartPage", () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it("shows loading state initially", () => {
    vi.mocked(api.getCart).mockReturnValue(new Promise(() => {}))
    render(<CartPage />)
    expect(screen.getByText(/Loading cart/)).toBeInTheDocument()
  })

  it("displays cart items and total", async () => {
    vi.mocked(api.getCart).mockResolvedValue({
      items: [
        { id: 1, product_id: 10, product_name: "Laptop", quantity: 1, unit_price: "50000.00", subtotal: "50000.00" },
        { id: 2, product_id: 11, product_name: "Mouse", quantity: 2, unit_price: "1500.00", subtotal: "3000.00" },
      ],
      total: "53000.00",
    })
    render(<CartPage />)
    await waitFor(() => expect(screen.getByText("Laptop")).toBeInTheDocument())
    expect(screen.getByText("₹50000.00")).toBeInTheDocument()
    expect(screen.getByText("₹53000.00")).toBeInTheDocument()
  })

  it("updates quantity on change", async () => {
    vi.mocked(api.getCart).mockResolvedValue({
      items: [{ id: 1, product_id: 10, product_name: "Laptop", quantity: 1, unit_price: "50000.00", subtotal: "50000.00" }],
      total: "50000.00",
    })
    vi.mocked(api.updateCartItem).mockResolvedValue({
      items: [{ id: 1, product_id: 10, product_name: "Laptop", quantity: 2, unit_price: "50000.00", subtotal: "100000.00" }],
      total: "100000.00",
    })
    render(<CartPage />)
    await waitFor(() => expect(screen.getByText("Laptop")).toBeInTheDocument())
    const input = screen.getByRole("spinbutton")
    fireEvent.change(input, { target: { value: "2" } })
    await waitFor(() => expect(api.updateCartItem).toHaveBeenCalledWith(10, 2))
  })

  it("shows error when checkout fails", async () => {
    vi.mocked(api.getCart).mockResolvedValue({
      items: [],
      total: "0.00",
    })
    vi.mocked(api.checkout).mockRejectedValue(new Error("Out of stock"))
    render(<CartPage />)
    await waitFor(() => expect(screen.getByText(/Your cart is empty/)).toBeInTheDocument())
  })
})
