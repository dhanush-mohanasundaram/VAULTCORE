from app import models
from app.schemas import StatsOut


def list_users(db, limit=20, offset=0):
    return (
        db.query(models.User)
        .order_by(models.User.created_at.desc())
        .limit(min(max(limit, 1), 100))
        .offset(max(offset, 0))
        .all()
    )


def admin_list_products(db):
    return db.query(models.Product).order_by(models.Product.created_at.desc()).all()


def admin_list_orders(db, limit=20, offset=0):
    return (
        db.query(models.Order)
        .join(models.User, models.User.id == models.Order.user_id)
        .order_by(models.Order.created_at.desc())
        .limit(min(max(limit, 1), 100))
        .offset(max(offset, 0))
        .all()
    )


def admin_stats(db) -> StatsOut:
    total_customers = db.query(models.User).filter(
        db.query(models.UserRole).filter(models.UserRole.user_id == models.User.id).exists()
    ).count() if False else db.query(models.User).count()
    total_products = db.query(models.Product).count()
    total_orders = db.query(models.Order).count()
    pending_orders = db.query(models.Order).filter(models.Order.status == "pending").count()
    completed_orders = db.query(models.Order).filter(models.Order.status == "completed").count()
    low_stock_alerts = (
        db.query(models.Inventory)
        .join(models.Product)
        .filter(models.Inventory.quantity <= 5, models.Product.is_active == 1)
        .count()
    )
    return StatsOut(
        total_customers=total_customers,
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        low_stock_alerts=low_stock_alerts,
    )


def admin_set_order_status(db, order_id: int, status: str):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    order.status = status
    db.commit()
    db.refresh(order)
    return order
