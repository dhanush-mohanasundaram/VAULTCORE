from fastapi import APIRouter, Depends, HTTPException, status
from app import schemas
from app.services import product_service
from app.deps import get_db, get_current_user, require_role
from sqlalchemy.orm import Session
from app import models

router = APIRouter()


def product_out(db: Session, p: models.Product) -> schemas.ProductOut:
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == p.id).first()
    cat = db.query(models.Category).filter(models.Category.id == p.category_id).first() if p.category_id else None
    return schemas.ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        price=p.price,
        sku=p.sku,
        category_id=p.category_id,
        stock=inv.quantity if inv else 0,
        is_active=bool(p.is_active),
        category_name=cat.name if cat else None,
        created_at=p.created_at,
    )


@router.get("", response_model=list[schemas.ProductOut])
def list_products(
    db: Session = Depends(get_db),
    category_id: int | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    products = product_service.list_products(db, category_id=category_id, search=search, limit=limit, offset=offset)
    return [product_out(db, p) for p in products]


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = product_service.get_product(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_out(db, p)


@router.post("", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    return product_out(db, product_service.create_product(db, data))


@router.patch("/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    data: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    p = product_service.update_product(db, product_id, data)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_out(db, p)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    ok = product_service.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return None


@router.post("/seed", status_code=status.HTTP_201_CREATED)
def seed_demo(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    """One-time demo seed: categories + sample products with inventory."""
    cats = {
        "Electronics": product_service.create_product if False else None,
    }
    # categories
    elec = models.Category(name="Electronics", slug="electronics", description="Gadgets and computers")
    furniture = models.Category(name="Furniture", slug="furniture", description="Home and office furniture")
    db.add_all([elec, furniture])
    db.flush()
    samples = [
        ("Laptop", "15-inch laptop, 16GB RAM", "50000.00", "SKU-LAP-001", elec.id, 10),
        ("Headphones", "Noise-cancelling wireless", "8000.00", "SKU-HP-002", elec.id, 20),
        ("Desk", "Wooden office desk", "12000.00", "SKU-DESK-003", furniture.id, 3),
        ("Chair", "Ergonomic office chair", "9000.00", "SKU-CHAIR-004", furniture.id, 1),
    ]
    for name, desc, price, sku, cat_id, stock in samples:
        existing = db.query(models.Product).filter(models.Product.sku == sku).first()
        if existing:
            continue
        product_service.create_product(
            db,
            schemas.ProductCreate(name=name, description=desc, price=price, sku=sku, category_id=cat_id, stock=stock),
        )
    return {"seeded": True}
