from app import models
from app.schemas import ProductCreate, ProductUpdate


def list_products(db, category_id=None, active_only=True):
    q = db.query(models.Product)
    if active_only:
        q = q.filter(models.Product.is_active == 1)
    if category_id is not None:
        q = q.filter(models.Product.category_id == category_id)
    return q.all()


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
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if inv:
        db.delete(inv)
    db.delete(product)
    db.commit()
    return True


def adjust_inventory(db, product_id: int, quantity: int, set_absolute: bool = False):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        inv = models.Inventory(product_id=product_id, quantity=0)
        db.add(inv)
        db.flush()
    if set_absolute:
        inv.quantity = quantity
    else:
        inv.quantity = (inv.quantity or 0) + quantity
    if inv.quantity < 0:
        inv.quantity = 0
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
