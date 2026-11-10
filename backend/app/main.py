from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import auth, products, cart, orders, admin

app = FastAPI(title="VAULTCORE — Secure Transaction-Safe E-Commerce API")

# CORS origins from config. No wildcard origin when credentials are enabled.
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health():
    return {"status": "ok"}
