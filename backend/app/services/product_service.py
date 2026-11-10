from app import models
from app.schemas import ProductCreate, ProductUpdate


def list_products(db, category_id=None, active_only=True, search=None, limit=20, offset=0):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.is_active == 1)
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            models.Product.name.ilike(like) | models.Product.description.ilike(like)
        )
    return query.order_by(models.Product.id).limit(limit).offset(offset).all()


def get_product(db, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def create_product(db, data: ProductCreate):
    product = models.Product(
        name=data.name,
        description=data.description,
        price=data.price,
        sku=data.sku,
        category_id=data.category_id,
        is_active=1 if data.is_active else 0,
    )
    db.add(product)
    db.flush()
    db.add(models.Inventory(product_id=product.id, quantity=data.stock))
    db.commit()
    db.refresh(product)
    return product


def update_product(db, product_id: int, data: ProductUpdate):
    product = get_product(db, product_id)
    if not product:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "is_active" and value is not None:
            setattr(product, field, 1 if value else 0)
        elif field == "stock" and value is not None:
            inv = (
                db.query(models.Inventory)
                .filter(models.Inventory.product_id == product.id)
                .first()
            )
            if not inv:
                inv = models.Inventory(product_id=product.id, quantity=0)
                db.add(inv)
                db.flush()
            inv.quantity = max(0, int(value))
        elif value is not None:
            setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db, product_id: int) -> bool:
    product = get_product(db, product_id)
    if not product:
        return False
    # Soft delete: keep order/cart history intact, just hide from catalog.
    product.is_active = 0
    db.commit()
    db.refresh(product)
    return True


def adjust_inventory(db, product_id: int, quantity: int, changed_by_user_id: int | None = None, reason: str | None = None):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        inv = models.Inventory(product_id=product_id, quantity=0)
        db.add(inv)
        db.flush()
    previous = inv.quantity or 0
    new_qty = previous + quantity
    if new_qty < 0:
        new_qty = 0
    inv.quantity = new_qty
    db.add(
        models.InventoryAuditLog(
            product_id=product_id,
            changed_by_user_id=changed_by_user_id,
            previous_quantity=previous,
            new_quantity=new_qty,
            reason=reason,
        )
    )
    db.commit()
    db.refresh(inv)
    return inv


def list_low_stock(db, threshold: int = 5):
    return (
        db.query(models.Inventory)
        .join(models.Product)
        .filter(models.Inventory.quantity <= threshold, models.Product.is_active == 1)
        .all()
    )
