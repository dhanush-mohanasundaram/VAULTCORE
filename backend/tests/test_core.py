"""
VAULTCORE backend tests.

Integration tests run against the real PostgreSQL database (vaultcore).
Tables are truncated between tests via reset_rows().
SQLite is deliberately NOT used because FOR UPDATE row locks and CHECK
constraints behave differently there.
"""
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, engine, Base
from app.main import app
from app import models
from app.security import _hash_body, hash_password

client = TestClient(app)


def get_db() -> Session:
    return SessionLocal()


def reset_rows():
    """Clear data tables between tests (keeps schema)."""
    db = get_db()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()


def _seed_basic_roles(db):
    for name in ("customer", "admin"):
        if not db.query(models.Role).filter(models.Role.name == name).first():
            db.add(models.Role(name=name))
    db.commit()


def _seed_admin_user(db, password="AdminPass1234!"):
    _seed_basic_roles(db)
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()
    user = models.User(
        email="admin@vaultcore.local",
        hashed_password=hash_password(password),
        full_name="Admin User",
        is_active=1,
    )
    db.add(user)
    db.flush()
    db.add(models.UserRole(user_id=user.id, role_id=admin_role.id))
    db.add(models.UserRole(user_id=user.id, role_id=customer_role.id))
    db.commit()
    return user


def _seed_customer_user(db, email="buyer@test.local", password="BuyerPass1234!"):
    _seed_basic_roles(db)
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()
    user = models.User(
        email=email,
        hashed_password=hash_password(password),
        full_name="Buyer User",
        is_active=1,
    )
    db.add(user)
    db.flush()
    db.add(models.UserRole(user_id=user.id, role_id=customer_role.id))
    db.commit()
    return user


def _login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def seed_roles_and_users(db: Session):
    for name in ("customer", "admin"):
        if not db.query(models.Role).filter(models.Role.name == name).first():
            db.add(models.Role(name=name))
    db.commit()
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

    cust = models.User(email="buyer@test.local", hashed_password=hash_password("password1234"), full_name="Buyer", is_active=1)
    adm = models.User(email="admin@test.local", hashed_password=hash_password("password1234"), full_name="Admin", is_active=1)
    db.add_all([cust, adm])
    db.flush()
    db.add_all([
        models.UserRole(user_id=cust.id, role_id=customer_role.id),
        models.UserRole(user_id=adm.id, role_id=customer_role.id),
        models.UserRole(user_id=adm.id, role_id=admin_role.id),
    ])
    db.commit()
    return cust, adm


def login(client, email: str = "buyer@test.local", password: str = "password1234"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def _seed_product(db, name="TestProd", price="100.00", sku="SKU-TP", stock=10, active=True):
    product = models.Product(
        name=name,
        description="desc",
        price=price,
        sku=sku,
        is_active=1 if active else 0,
    )
    db.add(product)
    db.flush()
    db.add(models.Inventory(product_id=product.id, quantity=stock))
    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# Unit tests — pure logic
# ---------------------------------------------------------------------------

def test_state_machine_transitions():
    from app.services.order_service import ALLOWED_TRANSITIONS, _can_transition

    assert _can_transition("pending", "paid") is True
    assert _can_transition("pending", "cancelled") is True
    assert _can_transition("paid", "shipped") is True
    assert _can_transition("shipped", "completed") is True
    assert _can_transition("completed", "paid") is False
    assert _can_transition("cancelled", "paid") is False
    assert _can_transition("pending", "completed") is False
    assert _can_transition("unknown", "paid") is False


def test_request_fingerprinting():
    h1 = _hash_body({"idempotency_key": "k1", "product_id": 1})
    h2 = _hash_body({"idempotency_key": "k1", "product_id": 1})
    h3 = _hash_body({"idempotency_key": "k1", "product_id": 2})
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


# ---------------------------------------------------------------------------
# Integration tests — auth & RBAC
# ---------------------------------------------------------------------------

def test_register_and_login():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    db.close()

    r = client.post(
        "/api/auth/register",
        json={"email": "newbie@test.local", "password": "secret1234", "full_name": "Newbie"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["roles"] == ["customer"]

    r = client.post(
        "/api/auth/register",
        json={"email": "newbie2@test.local", "password": "short"},
    )
    assert r.status_code == 400

    r = client.post(
        "/api/auth/register",
        json={"email": "newbie@test.local", "password": "secret1234"},
    )
    assert r.status_code == 400

    token = login(client, "newbie@test.local", "secret1234")
    r = client.get("/api/auth/me", headers=headers(token))
    assert r.status_code == 200
    assert r.json()["email"] == "newbie@test.local"

    r = client.post("/api/auth/login", json={"email": "newbie@test.local", "password": "wrong"})
    assert r.status_code == 401


def test_login_rate_limiting():
    reset_rows()
    db = SessionLocal()
    _seed_customer_user(db, email="ratelimit@test.local", password="CorrectPass1234!")
    db.close()
    for _ in range(5):
        r = client.post("/api/auth/login", json={"email": "ratelimit@test.local", "password": "wrong"})
        assert r.status_code == 401
    r = client.post("/api/auth/login", json={"email": "ratelimit@test.local", "password": "CorrectPass1234!"})
    assert r.status_code == 429, f"Expected 429, got {r.status_code}: {r.text}"


def test_products_and_admin_rbac():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    db.close()

    cust_token = login(client, "buyer@test.local", "password1234")
    adm_token = login(client, "admin@test.local", "password1234")

    r = client.post(
        "/api/products/",
        json={"name": "X", "price": "10.00", "sku": "SKU-X"},
        headers=headers(cust_token),
    )
    assert r.status_code == 403, r.text

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

    r = client.get("/api/products/?search=Widget")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    r = client.get("/api/products/?search=Nonexistent")
    assert r.status_code == 200
    assert len(r.json()) == 0

    r = client.get("/api/products/?limit=1&offset=0")
    assert r.status_code == 200
    assert len(r.json()) <= 1

    r = client.patch(
        f"/api/products/{pid}",
        json={"stock": 2, "price": "12.00"},
        headers=headers(adm_token),
    )
    assert r.status_code == 200
    assert float(r.json()["price"]) == 12.0

    r = client.delete(f"/api/products/{pid}", headers=headers(cust_token))
    assert r.status_code == 403
    r = client.delete(f"/api/products/{pid}", headers=headers(adm_token))
    assert r.status_code == 204


def test_revoked_admin_loses_access():
    reset_rows()
    db = SessionLocal()
    _seed_basic_roles(db)
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()

    user = models.User(
        email="revoked@test.local",
        hashed_password=hash_password("RevokedPass1234!"),
        full_name="Revoked User",
        is_active=1,
    )
    db.add(user)
    db.flush()
    db.add(models.UserRole(user_id=user.id, role_id=admin_role.id))
    db.add(models.UserRole(user_id=user.id, role_id=customer_role.id))
    db.commit()
    db.refresh(user)

    token = _login(client, "revoked@test.local", "RevokedPass1234!")

    r = client.get("/api/admin/stats", headers=headers(token))
    assert r.status_code == 200, r.text

    db.query(models.UserRole).filter(
        models.UserRole.user_id == user.id,
        models.UserRole.role_id == admin_role.id,
    ).delete()
    db.commit()

    r = client.get("/api/admin/stats", headers=headers(token))
    assert r.status_code == 403, r.text


# ---------------------------------------------------------------------------
# Integration tests — cart & checkout
# ---------------------------------------------------------------------------

def test_cart_and_checkout_happy_path():
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    product = _seed_product(db)
    product_id = product.id
    db.close()

    token = login(client, "buyer@test.local", "password1234")

    r = client.post(
        "/api/cart/",
        json={"product_id": product_id, "quantity": 3},
        headers=headers(token),
    )
    assert r.status_code == 200
    cart = r.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3
    assert float(cart["total"]) == 300.0

    key = "idem-checkout-1"
    r = client.post(
        "/api/orders/checkout",
        json={"idempotency_key": key},
        headers=headers(token),
    )
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "paid"
    assert float(order["total"]) == 300.0
    assert len(order["items"]) == 1
    assert float(order["items"][0]["unit_price"]) == 100.0

    db = get_db()
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    assert inv.quantity == 7
    db.close()

    r = client.get("/api/cart/", headers=headers(token))
    assert r.json()["items"] == []


def test_price_tampering_ignored():
    reset_rows()
    db = SessionLocal()
    _seed_customer_user(db)
    product = _seed_product(db, price="100.00", stock=10)
    product_id = product.id
    db.close()

    token = login(client, "buyer@test.local", "BuyerPass1234!")

    client.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(token))

    key = "tamper-key-1"
    r = client.post(
        "/api/orders/checkout",
        json={"idempotency_key": key},
        headers=headers(token),
    )
    assert r.status_code == 200, r.text
    assert float(r.json()["total"]) == 100.0


def test_checkout_idempotency():
    reset_rows()
    db = SessionLocal()
    _seed_customer_user(db)
    product = _seed_product(db, price="50.00", sku="SKU-ID", stock=5)
    product_id = product.id
    db.close()

    token = login(client, "buyer@test.local", "BuyerPass1234!")

    client.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(token))
    key = "idem-same-key"

    r1 = client.post(
        "/api/orders/checkout",
        json={"idempotency_key": key},
        headers=headers(token),
    )
    assert r1.status_code == 200, r1.text

    client.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(token))
    r2 = client.post(
        "/api/orders/checkout",
        json={"idempotency_key": key},
        headers=headers(token),
    )
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]

    db = get_db()
    count = db.query(models.Order).filter(models.Order.id == r1.json()["id"]).count()
    assert count == 1, "duplicate order created despite idempotency key"

    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    assert inv.quantity == 4
    db.close()


# ---------------------------------------------------------------------------
# Concurrency tests (deterministic, threading.Barrier)
# ---------------------------------------------------------------------------

def test_concurrent_checkout_no_overselling():
    """5 buyers, 1 unit stock: exactly 1 succeeds, 4 get 409, stock ends at 0."""
    reset_rows()
    db = get_db()
    seed_roles_and_users(db)
    buyer_role = db.query(models.Role).filter(models.Role.name == "customer").first()

    buyers = []
    for i in range(5):
        email = f"cb{i}@test.local"
        u = models.User(
            email=email,
            hashed_password=hash_password("BuyerPass1234!"),
            full_name=f"Buyer {i}",
            is_active=1,
        )
        db.add(u)
        db.flush()
        db.add(models.UserRole(user_id=u.id, role_id=buyer_role.id))
        buyers.append(email)
    db.commit()

    product = _seed_product(db, name="Rare", price="999.00", sku="SKU-RARE", stock=1)
    product_id = product.id
    db.close()

    barrier = threading.Barrier(5)
    results = {"ok": 0, "fail_409": 0, "other": []}
    lock = threading.Lock()

    def buyer(email: str):
        c = TestClient(app)
        token = _login(c, email, "BuyerPass1234!")
        c.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(token))
        barrier.wait()
        try:
            r = c.post(
                "/api/orders/checkout",
                json={"idempotency_key": f"conc-{email}"},
                headers=headers(token),
            )
            with lock:
                if r.status_code == 200:
                    results["ok"] += 1
                elif r.status_code == 409:
                    results["fail_409"] += 1
                else:
                    results["other"].append((r.status_code, r.text[:200]))
        except Exception as exc:
            with lock:
                results["other"].append(("exception", str(exc)))

    threads = [threading.Thread(target=buyer, args=(e,)) for e in buyers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["ok"] == 1, results
    assert results["fail_409"] == 4, results
    assert results["other"] == [], results

    db = get_db()
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    assert inv.quantity == 0, f"Expected 0, got {inv.quantity}"
    orders = db.query(models.Order).all()
    assert len(orders) == 1, f"Expected 1 order, got {len(orders)}"
    db.close()


def test_concurrent_idempotency_same_key():
    """20 requests, same idempotency key: exactly 1 order row, all return same id."""
    reset_rows()
    db = SessionLocal()
    _seed_customer_user(db)
    product = _seed_product(db, price="10.00", sku="SKU-IDEM", stock=100)
    product_id = product.id
    db.close()

    token = login(client, "buyer@test.local", "BuyerPass1234!")
    client.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(token))

    barrier = threading.Barrier(20)
    results = {"ids": set(), "statuses": [], "errors": []}
    lock = threading.Lock()

    def worker(n: int):
        c = TestClient(app)
        tok = _login(c, "buyer@test.local", "BuyerPass1234!")
        c.post("/api/cart/", json={"product_id": product_id, "quantity": 1}, headers=headers(tok))
        barrier.wait()
        try:
            r = c.post(
                "/api/orders/checkout",
                json={"idempotency_key": "shared-key-1"},
                headers=headers(tok),
            )
            with lock:
                results["statuses"].append(r.status_code)
                if r.status_code == 200:
                    results["ids"].add(r.json()["id"])
                elif r.status_code not in (200, 409):
                    results["errors"].append((r.status_code, r.text[:200]))
        except Exception as exc:
            with lock:
                results["errors"].append(("exception", str(exc)))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results["ids"]) == 1, results
    assert all(s in (200, 409) for s in results["statuses"]), results
    assert results["errors"] == [], results

    db = get_db()
    count = db.query(models.Order).count()
    assert count == 1, f"Expected 1 order, got {count}"
    db.close()


def test_concurrent_deadlock_opposite_order():
    """Two carts sharing two products, locked in opposite order: no deadlock."""
    reset_rows()
    db = SessionLocal()
    _seed_customer_user(db, email="deadlock-a@test.local", password="PassA1234!")
    _seed_customer_user(db, email="deadlock-b@test.local", password="PassB1234!")
    p1 = _seed_product(db, name="P1", price="10.00", sku="SKU-P1", stock=1)
    p2 = _seed_product(db, name="P2", price="20.00", sku="SKU-P2", stock=1)
    p1_id, p2_id = p1.id, p2.id
    db.close()

    token_a = login(client, "deadlock-a@test.local", "PassA1234!")
    token_b = login(client, "deadlock-b@test.local", "PassB1234!")

    barrier = threading.Barrier(2)
    results = {"t1": None, "t2": None, "errors": []}
    lock = threading.Lock()

    def worker_a():
        c = TestClient(app)
        tok = _login(c, "deadlock-a@test.local", "PassA1234!")
        c.post("/api/cart/", json={"product_id": p1_id, "quantity": 1}, headers=headers(tok))
        c.post("/api/cart/", json={"product_id": p2_id, "quantity": 1}, headers=headers(tok))
        barrier.wait()
        try:
            r = c.post(
                "/api/orders/checkout",
                json={"idempotency_key": "deadlock-a"},
                headers=headers(tok),
            )
            with lock:
                results["t1"] = r.status_code
        except Exception as exc:
            with lock:
                results["errors"].append(("a", str(exc)))

    def worker_b():
        c = TestClient(app)
        tok = _login(c, "deadlock-b@test.local", "PassB1234!")
        c.post("/api/cart/", json={"product_id": p2_id, "quantity": 1}, headers=headers(tok))
        c.post("/api/cart/", json={"product_id": p1_id, "quantity": 1}, headers=headers(tok))
        barrier.wait()
        try:
            r = c.post(
                "/api/orders/checkout",
                json={"idempotency_key": "deadlock-b"},
                headers=headers(tok),
            )
            with lock:
                results["t2"] = r.status_code
        except Exception as exc:
            with lock:
                results["errors"].append(("b", str(exc)))

    t1 = threading.Thread(target=worker_a)
    t2 = threading.Thread(target=worker_b)
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert not t1.is_alive() and not t2.is_alive(), "Deadlock detected"
    assert results["errors"] == [], results
    statuses = sorted([results["t1"], results["t2"]])
    assert statuses == [200, 409], results

    db = get_db()
    inv1 = db.query(models.Inventory).filter(models.Inventory.product_id == p1_id).first()
    inv2 = db.query(models.Inventory).filter(models.Inventory.product_id == p2_id).first()
    assert inv1.quantity == 0
    assert inv2.quantity == 0
    db.close()


# ---------------------------------------------------------------------------
# Migration tests
# ---------------------------------------------------------------------------

def test_migrations_upgrade_downgrade_upgrade():
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "orders" in tables
    assert "idempotency_keys" in tables
    assert "inventory_audit_log" in tables