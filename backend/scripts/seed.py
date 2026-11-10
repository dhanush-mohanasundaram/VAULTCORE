"""Seed roles, admin user, and demo catalog. Idempotent: safe to re-run."""
from app.database import SessionLocal, engine
from app import models
from app.services import product_service
from app.schemas import ProductCreate
from app.security import hash_password

db = SessionLocal()

for name in ("customer", "admin"):
    if not db.query(models.Role).filter(models.Role.name == name).first():
        db.add(models.Role(name=name))
db.commit()

admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()

admin = db.query(models.User).filter(models.User.email == "admin@vaultcore.local").first()
if not admin:
    admin = models.User(
        email="admin@vaultcore.local",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        is_active=1,
    )
    db.add(admin)
    db.flush()
for r in (admin_role, customer_role):
    if not db.query(models.UserRole).filter_by(user_id=admin.id, role_id=r.id).first():
        db.add(models.UserRole(user_id=admin.id, role_id=r.id))
db.commit()

samples = [
    ("Laptop", "15-inch laptop, 16GB RAM", "50000.00", "SKU-LAP-001", "Electronics", 10),
    ("Headphones", "Noise-cancelling wireless", "8000.00", "SKU-HP-002", "Electronics", 20),
    ("Desk", "Wooden office desk", "12000.00", "SKU-DESK-003", "Furniture", 3),
    ("Chair", "Ergonomic office chair", "9000.00", "SKU-CHAIR-004", "Furniture", 1),
    ("Mouse", "Wireless optical mouse", "1500.00", "SKU-MSE-005", "Electronics", 50),
]
for name, desc, price, sku, cat_name, stock in samples:
    cat = db.query(models.Category).filter(models.Category.name == cat_name).first()
    if not cat:
        cat = models.Category(name=cat_name, slug=cat_name.lower(), description=f"{cat_name} category")
        db.add(cat)
        db.flush()
    if db.query(models.Product).filter(models.Product.sku == sku).first():
        continue
    product_service.create_product(db, ProductCreate(name=name, description=desc, price=price, sku=sku, category_id=cat.id, stock=stock))

print("Seed complete: admin@vaultcore.local / admin123 (admin + customer), customer role available.")
db.close()
