from app import models


def get_or_create_cart(db, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        cart = models.Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_to_cart(db, user_id: int, product_id: int, quantity: int):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id, models.Product.is_active == 1)
        .first()
    )
    if not product:
        return None
    cart = get_or_create_cart(db, user_id)
    item = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == product_id)
        .first()
    )
    if item:
        item.quantity += quantity
    else:
        item = models.CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db, user_id: int, product_id: int, quantity: int):
    cart = get_or_create_cart(db, user_id)
    item = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == product_id)
        .first()
    )
    if not item:
        return None
    if quantity <= 0:
        db.delete(item)
        db.commit()
        return True
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def remove_from_cart(db, user_id: int, product_id: int):
    return update_cart_item(db, user_id, product_id, 0)


def clear_cart(db, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if cart:
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()


def get_cart(db, user_id: int):
    cart = get_or_create_cart(db, user_id)
    items = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id)
        .join(models.Product, models.Product.id == models.CartItem.product_id)
        .all()
    )
    result = []
    total = 0
    for item in items:
        p = item.product
        unit_price = p.price
        subtotal = unit_price * item.quantity
        total += subtotal
        result.append(
            {
                "id": item.id,
                "product_id": p.id,
                "product_name": p.name,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )
    return {"items": result, "total": total}
