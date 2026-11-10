from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


# ---------- Auth ----------
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    roles: list[str] = []

    model_config = ConfigDict(from_attributes=True)


# ---------- Categories ----------
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True


class CategoryOut(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Products ----------
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: Optional[str] = None
    category_id: Optional[int] = None
    stock: int = 0
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    category_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Cart ----------
class CartItemIn(BaseModel):
    product_id: int
    quantity: int


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartOut(BaseModel):
    items: list[CartItemOut] = []
    total: Decimal = Decimal("0.00")


# ---------- Orders ----------
class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    status: str
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class CheckoutRequest(BaseModel):
    idempotency_key: str


# ---------- Admin ----------
class AdminOrderOut(BaseModel):
    id: int
    customer_email: str
    status: str
    total: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total_customers: int
    total_products: int
    total_orders: int
    pending_orders: int
    completed_orders: int
    low_stock_alerts: int
