from fastapi import HTTPException, status
from sqlalchemy import text
from app import models

# Allowed order status transitions.
# pending -> paid -> shipped -> completed
# pending -> cancelled
# paid -> shipped (admin marks shipped)
# shipped -> completed (admin marks completed)
# paid -> cancelled (refund)
ALLOWED_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


def _hash_body(body: dict | None) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(body or {}, sort_keys=True).encode()).hexdigest()


def checkout(db, user, idempotency_key: str, request_body: dict | None = None):
    """
    Transaction-safe checkout.

    Order of operations (commented to explain the why):
    1. Fast-path idempotency check BEFORE taking row locks — returns the stored
       result immediately for repeat requests, avoiding lock contention.
    2. Load cart and its items.
    3. Lock product and inventory rows in ASCENDING id order (SELECT ... FOR
       UPDATE) — deterministic lock ordering prevents deadlocks when two
       transactions touch overlapping products in different sequences.
    4. Re-check idempotency INSIDE the transaction — the fast-path check could
       have raced with another transaction that committed between step 1 and the
       lock acquisition.
    5. Validate products are active and stock is sufficient.
    6. Snapshot unit prices from the DB into order_items — client prices ignored.
    7. Conditional stock decrement: UPDATE ... SET quantity = quantity - n WHERE
       product_id = ? AND quantity >= n; rowcount must equal 1.
    8. Insert order + idempotency record + clear cart, all in one transaction.
    9. Commit. On any failure, rollback.
    """
    # 1. Fast-path idempotency check (no locks held yet).
    body_hash = _hash_body(request_body)
    existing = (
        db.query(models.IdempotencyKey)
        .filter(models.IdempotencyKey.user_id == user.id, models.IdempotencyKey.key == idempotency_key)
        .first()
    )
    if existing and existing.order_id:
        order = db.query(models.Order).filter(models.Order.id == existing.order_id).first()
        if order:
            return order

    # 2. Load cart with items inside the transaction.
    cart = db.query(models.Cart).filter(models.Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 3. Row-level locks in ascending id order to prevent deadlocks.
    product_ids = sorted({item.product_id for item in cart.items})
    products = {
        p.id: p
        for p in db.query(models.Product)
        .filter(models.Product.id.in_(product_ids))
        .order_by(models.Product.id)
        .with_for_update()
        .all()
    }
    inventories = {
        inv.product_id: inv
        for inv in db.query(models.Inventory)
        .filter(models.Inventory.product_id.in_(product_ids))
        .order_by(models.Inventory.product_id)
        .with_for_update()
        .all()
    }

    # 4. Re-check idempotency inside the transaction (post-lock).
    existing = (
        db.query(models.IdempotencyKey)
        .filter(models.IdempotencyKey.user_id == user.id, models.IdempotencyKey.key == idempotency_key)
        .first()
    )
    if existing and existing.order_id:
        order = db.query(models.Order).filter(models.Order.id == existing.order_id).first()
        if order:
            return order

    # 5. Validate products active and stock sufficient.
    total = 0
    order_items = []
    for item in cart.items:
        p = products.get(item.product_id)
        if not p or p.is_active != 1:
            raise HTTPException(status_code=409, detail=f"Product {item.product_id} is unavailable")
        inv = inventories.get(item.product_id)
        if not inv:
            raise HTTPException(status_code=409, detail=f"Out of stock: {p.name}")
        if (inv.quantity or 0) < item.quantity:
            raise HTTPException(status_code=409, detail=f"Out of stock: {p.name}")
        line_total = p.price * item.quantity
        total += line_total
        order_items.append((p, item.quantity, p.price))

    # 6 & 7. Write order + conditional stock decrement + idempotency record.
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
        # Conditional decrement: only if quantity >= qty. Guarantees no
        # overselling even if locks are somehow bypassed.
        result = db.execute(
            text(
                "UPDATE inventory SET quantity = quantity - :qty "
                "WHERE product_id = :pid AND quantity >= :qty"
            ),
            {"qty": qty, "pid": p.id},
        )
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail=f"Out of stock: {p.name}")

    db.add(
        models.IdempotencyKey(
            key=idempotency_key,
            user_id=user.id,
            request_body_hash=body_hash,
            order_id=order.id,
            response_status_code=200,
            response_body=None,
        )
    )

    # Empty the cart after successful checkout.
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()

    try:
        db.commit()
    except Exception:
        db.rollback()
        # Unique constraint on (user_id, key) means a concurrent request won
        # with the same key. Fetch and return that order instead of erroring.
        existing = (
            db.query(models.IdempotencyKey)
            .filter(models.IdempotencyKey.user_id == user.id, models.IdempotencyKey.key == idempotency_key)
            .first()
        )
        if existing and existing.order_id:
            order = db.query(models.Order).filter(models.Order.id == existing.order_id).first()
            if order:
                return order
        raise

    db.refresh(order)
    return order


def _can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def set_order_status(db, order_id: int, status: str):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    if not _can_transition(order.status, status):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition order {order_id} from '{order.status}' to '{status}'",
        )
    order.status = status
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
