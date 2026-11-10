import threading
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.main import app
from app import models
from app.security import hash_password
from app.services import auth_service

client = TestClient(app)


def get_db() -> Session:
    return SessionLocal()


def reset_rows():
    """Clear data tables between tests (keeps schema)."""
    db = get_db()
    for table in (
        models.IdempotencyKey.__table__,
        models.OrderItem.__table__,
        models.Order.__table__,
        models.CartItem.__table__,
        models.Cart.__table__,
        models.Inventory.__table__,
        models.Product.__table__,
        models.Category.__table__,
        models.UserRole.__table__,
        models.User.__table__,
        models.Role.__table__,
    ):
        db.execute(table.delete())
    db.commit()
    db.close()


def seed_roles_and_users(db: Session):
    for name in ("customer", "admin"):
        if not db.query(models.Role).filter(models.Role.name == name).first():
            db.add(models.Role(name=name))
    db.commit()
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

    cust = models.User(email="buyer@test.local", hashed_password=hash_password("pw"), full_name="Buyer", is_active=1)
    adm = models.User(email="admin@test.local", hashed_password=hash_password("pw"), full_name="Admin", is_active=1)
    db.add_all([cust, adm])
    db.flush()
    db.add_all([
        models.UserRole(user_id=cust.id, role_id=customer_role.id),
        models.UserRole(user_id=adm.id, role_id=customer_role.id),
        models.UserRole(user_id=adm.id, role_id=admin_role.id),
    ])
    db.commit()
    return cust, adm


def login(email: str = "buyer@test.local", password: str = "pw"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    db.close()

    r = client.post(
        "/api/auth/register",
        json={"email": "newbie@test.local", "password": "secret", "full_name": "Newbie"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["roles"] == ["customer"]

    r = client.post("/api/auth/register", json={"email": "newbie@test.local", "password": "secret"})
    assert r.status_code == 400

    token = login("newbie@test.local", "secret")
    r = client.get("/api/auth/me", headers=headers(token))
    assert r.status_code == 200
    assert r.json()["email"] == "newbie@test.local"
    assert "customer" in r.json()["roles"]

    r = client.post("/api/auth/login", json={"email": "newbie@test.local", "password": "wrong"})
    assert r.status_code == 401


def test_products_and_admin_rbac():
    reset_rows()
    db = get_db()
    cust, adm = seed_roles_and_users(db)
    db.close()

    cust_token = login("buyer@test.local", "pw")
    adm_token = login("admin@test.local", "pw")

    # customer cannot create products
    r = client.post(
        "/api/products/",
        json={"name": "X", "price": "10.00", "sku": "SKU-X"},
        headers=headers(cust_token),
    )
    assert r.status_code == 403, r.text

    # admin creates
    r = client.post(
        "/api/products/",
        json={"name": "Widget", "price": "10.00", "sku": "SKU-W", "stock": 5},
        headers=headers(adm_token),
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r = client.get("/api/products/")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    r = client.get(f"/api/products/{pid}")
    assert r.status_code == 200 and r.json()["stock"] == 5

    r = client.patch(f"/api/products/{pid}", json={"stock": 2, "price": "12.00"}, headers=headers(adm_token))
    assert r.status_code == 200 and float(r.json()["price"]) == 12.0
    r = client.get(f"/api/products/{pid}")
    assert r.status_code == 200 and r.json()["stock"] == 2

    r = client.delete(f"/api/products/{pid}", headers=headers(cust_token))
    assert r.status_code == 403
    r = client.delete(f"/api/products/{pid}", headers=headers(adm_token))
    assert r.status_code == 204


def test_cart_and_checkout_happy_path():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    # product with stock
    prod = models.Product(name="TestProd", price="100.00", sku="SKU-TP", is_active=1)
    db.add(prod)
    db.flush()
    db.add(models.Inventory(product_id=prod.id, quantity=10))
    db.commit()
    prod_id = prod.id
    db.close()

    token = login()
    r = client.post("/api/cart/", json={"product_id": prod_id, "quantity": 3}, headers=headers(token))
    assert r.status_code == 200
    cart = r.json()
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 3
    assert cart["total"] == 300.0

    key = "idem-checkout-1"
    r = client.post("/api/orders/checkout", json={"idempotency_key": key}, headers=headers(token))
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "paid"
    assert float(order["total"]) == 300.0
    assert len(order["items"]) == 1
    assert float(order["items"][0]["unit_price"]) == 100.0

    # inventory decremented
    db = get_db()
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == prod_id).first()
    assert inv.quantity == 7
    # cart emptied
    r = client.get("/api/cart/", headers=headers(token))
    assert r.json()["items"] == []
    db.close()


def test_checkout_idempotency():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    prod = models.Product(name="IdemProd", price="50.00", sku="SKU-ID", is_active=1)
    db.add(prod)
    db.flush()
    db.add(models.Inventory(product_id=prod.id, quantity=5))
    db.commit()
    prod_id = prod.id
    db.close()

    token = login()
    client.post("/api/cart/", json={"product_id": prod_id, "quantity": 1}, headers=headers(token))
    key = "idem-same-key"
    r1 = client.post("/api/orders/checkout", json={"idempotency_key": key}, headers=headers(token))
    assert r1.status_code == 200
    # refill cart for second attempt
    client.post("/api/cart/", json={"product_id": prod_id, "quantity": 1}, headers=headers(token))
    r2 = client.post("/api/orders/checkout", json={"idempotency_key": key}, headers=headers(token))
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]

    db = get_db()
    n = db.query(models.Order).filter(models.Order.id == r1.json()["id"]).count()
    assert n == 1, "duplicate order created despite idempotency key"
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == prod_id).first()
    assert inv.quantity == 4
    db.close()


def test_concurrent_checkout_no_overselling():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    # Each buyer gets their own account so carts never get mixed up.
    buyers = []
    for i in range(5):
        email = f"concurrent buyer {i}@test.local".replace(" ", "")
        u = models.User(email=email, hashed_password=hash_password("pw"), full_name=f"Buyer {i}", is_active=1)
        db.add(u)
        db.flush()
        cr = db.query(models.Role).filter(models.Role.name == "customer").first()
        db.add(models.UserRole(user_id=u.id, role_id=cr.id))
        buyers.append((email, u.id))
    db.commit()
    prod = models.Product(name="Rare", price="999.00", sku="SKU-RARE", is_active=1)
    db.add(prod)
    db.flush()
    db.add(models.Inventory(product_id=prod.id, quantity=1))
    db.commit()
    prod_id = prod.id
    db.close()

    results = {"ok": 0, "fail": 0, "errors": []}
    lock = threading.Lock()

    def buyer(n: int):
        c = TestClient(app)
        email, _ = buyers[n]
        r = c.post("/api/auth/login", json={"email": email, "password": "pw"})
        assert r.status_code == 200, r.text
        tok = r.json()["access_token"]
        c.post("/api/cart/", json={"product_id": prod_id, "quantity": 1}, headers=headers(tok))
        try:
            r = c.post(
                "/api/orders/checkout",
                json={"idempotency_key": f"conc-{n}"},
                headers=headers(tok),
            )
            with lock:
                if r.status_code == 200:
                    results["ok"] += 1
                elif r.status_code == 409:
                    results["fail"] += 1
                else:
                    results["errors"].append((n, r.status_code, r.text[:200]))
        except Exception as exc:  # noqa: BLE001
            with lock:
                results["errors"].append((n, "exception", str(exc)))

    threads = [threading.Thread(target=buyer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["ok"] == 1, results
    assert results["fail"] == 4, results
    assert results["errors"] == [], results

    db = get_db()
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == prod_id).first()
    assert inv.quantity == 0
    orders = db.query(models.Order).all()
    assert len(orders) == 1
    db.close()


def test_admin_stats_and_low_stock():
    reset_rows()
    db = get_db()
    cust, adm = seed_roles_and_users(db)
    p1 = models.Product(name="Low1", price="1.00", sku="SKU-L1", is_active=1)
    p2 = models.Product(name="Low2", price="2.00", sku="SKU-L2", is_active=1)
    db.add_all([p1, p2])
    db.flush()
    db.add_all([models.Inventory(product_id=p1.id, quantity=2), models.Inventory(product_id=p2.id, quantity=1)])
    o = models.Order(user_id=cust.id, status="pending", total="1.00")
    db.add(o)
    db.commit()
    db.close()

    token = login("admin@test.local", "pw")
    r = client.get("/api/admin/stats", headers=headers(token))
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["total_products"] == 2
    assert s["total_orders"] == 1
    assert s["pending_orders"] == 1
    assert s["low_stock_alerts"] == 2

    r = client.get("/api/admin/low-stock", headers=headers(token))
    assert r.status_code == 200 and len(r.json()) == 2

    # customer forbidden
    ctok = login("buyer@test.local", "pw")
    r = client.get("/api/admin/stats", headers=headers(ctok))
    assert r.status_code == 403
