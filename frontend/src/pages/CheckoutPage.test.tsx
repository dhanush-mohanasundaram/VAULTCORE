import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import CheckoutPage from "./CheckoutPage"
import * as api from "../lib/api"

vi.mock("../lib/api", () => ({
  api: {
    checkout: vi.fn(),
  },
}))

describe("CheckoutPage", () => {
  beforeEach(() => {
    vi.resetAllMocks()
    sessionStorage.removeItem("vc_idem_key")
  })

  it("shows checkout form with idempotency key", () => {
    render(<CheckoutPage />)
    expect(screen.getByText(/Idempotency key/)).toBeInTheDocument()
    const keyInput = screen.getByRole("textbox")
    expect(keyInput.value).toMatch(/^vc-/)
  })

  it("generates a new key when New key button is clicked", async () => {
    render(<CheckoutPage />)
    const firstKey = screen.getByRole("textbox").value
    fireEvent.click(screen.getByText("New key"))
    expect(screen.getByRole("textbox").value).not.toBe(firstKey)
  })

  it("places order and shows success", async () => {
    vi.mocked(api.checkout).mockResolvedValue({
      id: 42,
      status: "paid",
      total: "300.00",
      created_at: "2026-11-10T10:00:00Z",
      items: [],
    })
    render(<CheckoutPage />)
    fireEvent.click(screen.getByText("Place order"))
    await waitFor(() => expect(screen.getByText(/Order placed/)).toBeInTheDocument())
    expect(screen.getByText("Order #42")).toBeInTheDocument()
  })

  it("shows error on checkout failure", async () => {
    vi.mocked(api.checkout).mockRejectedValue(new Error("Out of stock"))
    render(<CheckoutPage />)
    fireEvent.click(screen.getByText("Place order"))
    await waitFor(() => expect(screen.getByText(/Out of stock/)).toBeInTheDocument())
  })

  it("stores idempotency key in sessionStorage", async () => {
    vi.mocked(api.checkout).mockResolvedValue({
      id: 42, status: "paid", total: "300.00", created_at: "2026-11-10T10:00:00Z", items: [],
    })
    render(<CheckoutPage />)
    const key = screen.getByRole("textbox").value
    fireEvent.click(screen.getByText("Place order"))
    await waitFor(() => expect(screen.getByText(/Order placed/)).toBeInTheDocument())
    expect(sessionStorage.getItem("vc_idem_key")).toBeNull()
  })
})
