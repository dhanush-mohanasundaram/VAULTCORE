from fastapi import APIRouter, Depends, HTTPException
from app import schemas
from app.services import cart_service
from app.deps import get_db, get_current_user
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("", response_model=schemas.CartOut)
def get_cart(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    cart = cart_service.get_cart(db, current_user.id)
    return schemas.CartOut(items=cart["items"], total=cart["total"])


@router.post("")
def add_to_cart(data: schemas.CartItemIn, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    item = cart_service.add_to_cart(db, current_user.id, data.product_id, data.quantity)
    if item is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return cart_service.get_cart(db, current_user.id)


@router.patch("/{product_id}")
def update_cart_item(
    product_id: int,
    data: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = cart_service.update_cart_item(db, current_user.id, product_id, data.quantity)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return cart_service.get_cart(db, current_user.id)


@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    cart_service.remove_from_cart(db, current_user.id, product_id)
    return cart_service.get_cart(db, current_user.id)


@router.delete("")
def clear_cart(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    cart_service.clear_cart(db, current_user.id)
    return {"ok": True}
