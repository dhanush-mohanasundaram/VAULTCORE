from fastapi import APIRouter, Depends, HTTPException, Body
from app import schemas
from app.services import admin_service
from app.deps import get_db, get_current_user, require_role
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    from app.services import auth_service
    users = admin_service.list_users(db)
    result = []
    for u in users:
        roles = auth_service.get_user_role_names(db, u.id)
        result.append(schemas.UserOut(id=u.id, email=u.email, full_name=u.full_name, roles=roles))
    return result


@router.get("/products", response_model=list[schemas.ProductOut])
def admin_products(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    products = admin_service.admin_list_products(db)
    from app.api.products import product_out
    return [product_out(db, p) for p in products]


@router.get("/orders", response_model=list[schemas.AdminOrderOut])
def admin_orders(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    orders = admin_service.admin_list_orders(db)
    result = []
    for o in orders:
        result.append(
            schemas.AdminOrderOut(
                id=o.id,
                customer_email=o.user.email,
                status=o.status,
                total=o.total,
                created_at=o.created_at,
            )
        )
    return result


@router.patch("/orders/{order_id}/status", response_model=schemas.AdminOrderOut)
def set_order_status(
    order_id: int,
    status_in: str = Body(...),
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    order = admin_service.admin_set_order_status(db, order_id, status_in)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return schemas.AdminOrderOut(
        id=order.id, customer_email=order.user.email, status=order.status,
        total=order.total, created_at=order.created_at,
    )


@router.get("/stats", response_model=schemas.StatsOut)
def stats(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    return admin_service.admin_stats(db)


@router.get("/low-stock", response_model=list[schemas.ProductOut])
def low_stock(db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    from app.api.products import product_out
    from app.services import product_service
    rows = product_service.list_low_stock(db)
    return [product_out(db, r.product) for r in rows]
