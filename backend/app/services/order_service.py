from fastapi import HTTPException, status
from app import models


def checkout(db, user, idempotency_key: str):
    # 1. Idempotency: same key must never create a second order.
    existing = (
        db.query(models.IdempotencyKey)
        .filter(models.IdempotencyKey.key == idempotency_key)
        .first()
    )
    if existing:
        if existing.order_id:
            order = db.query(models.Order).filter(models.Order.id == existing.order_id).first()
            return order
        raise HTTPException(status_code=409, detail="Checkout already in progress for this key")

    # 2. Load cart with items + products inside the transaction.
    cart = db.query(models.Cart).filter(models.Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 3. Row-level locks on products and inventory so concurrent checkouts
    #    cannot oversell the same stock (SELECT ... FOR UPDATE).
    product_ids = [item.product_id for item in cart.items]
    products = {
        p.id: p
        for p in db.query(models.Product)
        .filter(models.Product.id.in_(product_ids))
        .with_for_update()
        .all()
    }
    inventories = {
        inv.product_id: inv
        for inv in db.query(models.Inventory)
        .filter(models.Inventory.product_id.in_(product_ids))
        .with_for_update()
        .all()
    }

    # 4. Validate stock and backend-computed prices (frontend prices are never trusted).
    total = 0
    order_items = []
    for item in cart.items:
        p = products.get(item.product_id)
        if not p or p.is_active != 1:
            raise HTTPException(status_code=409, detail=f"Product {item.product_id} is unavailable")
        inv = inventories.get(item.product_id)
        if not inv or (inv.quantity or 0) < item.quantity:
            raise HTTPException(status_code=409, detail=f"Out of stock: {p.name}")
        line_total = p.price * item.quantity
        total += line_total
        order_items.append((p, item.quantity, p.price))

    # 5. Write order + decrement inventory + record idempotency key, all or nothing.
    order = models.Order(user_id=user.id, status="paid", total=total)
    db.add(order)
    db.flush()
    for p, qty, unit_price in order_items:
        db.add(
            models.OrderItem(
                order_id=order.id,
                product_id=p.id,
                quantity=qty,
                unit_price=unit_price,
            )
        )
        inv = inventories[p.id]
        inv.quantity = (inv.quantity or 0) - qty
    db.add(models.IdempotencyKey(key=idempotency_key, user_id=user.id, order_id=order.id))

    # Empty the cart after successful checkout.
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()

    db.commit()
    db.refresh(order)
    return order


def list_orders(db, user, is_admin: bool = False):
    q = db.query(models.Order)
    if not is_admin:
        q = q.filter(models.Order.user_id == user.id)
    return q.order_by(models.Order.created_at.desc()).all()


def get_order(db, order_id: int, user, is_admin: bool = False):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    if not is_admin and order.user_id != user.id:
        return None
    return order


def admin_set_order_status(db, order_id: int, status: str):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    order.status = status
    db.commit()
    db.refresh(order)
    return order
