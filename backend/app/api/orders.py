from fastapi import APIRouter, Depends, HTTPException
from app import schemas
from app.services import order_service
from app.deps import get_db, get_current_user, require_role
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/checkout", response_model=schemas.OrderOut)
def checkout(
    data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        order = order_service.checkout(db, current_user, data.idempotency_key)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return _order_out(db, order)


@router.get("", response_model=list[schemas.OrderOut])
def list_orders(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    orders = order_service.list_orders(db, current_user, is_admin="admin" in [r for r in __import__("app.services.auth_service", fromlist=["get_user_role_names"]).get_user_role_names(db, current_user.id)])
    return [_order_out(db, o) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.services import auth_service
    roles = auth_service.get_user_role_names(db, current_user.id)
    order = order_service.get_order(db, order_id, current_user, is_admin="admin" in roles)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_out(db, order)


def _order_out(db: Session, order) -> schemas.OrderOut:
    items = []
    for it in order.items:
        items.append(
            schemas.OrderItemOut(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product.name,
                quantity=it.quantity,
                unit_price=it.unit_price,
                subtotal=it.unit_price * it.quantity,
            )
        )
    return schemas.OrderOut(
        id=order.id,
        status=order.status,
        total=order.total,
        created_at=order.created_at,
        items=items,
    )
