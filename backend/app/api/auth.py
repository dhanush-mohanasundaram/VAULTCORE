from fastapi import APIRouter, Depends, HTTPException, Request, status
from app import schemas
from app.services import auth_service
from app.deps import get_db, get_current_user, require_role
from app.security import create_access_token, is_login_rate_limited, register_login_attempt, login_rate_limit_key
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = auth_service.register(db, data)
    if user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    roles = auth_service.get_user_role_names(db, user.id)
    return schemas.UserOut(id=user.id, email=user.email, full_name=user.full_name, roles=roles)


@router.post("/login", response_model=schemas.Token)
def login(request: Request, data: schemas.UserLogin, db: Session = Depends(get_db)):
    identifier = login_rate_limit_key(request.client.host if request.client else None, data.email)
    if is_login_rate_limited(identifier):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    user = auth_service.authenticate(db, data.email, data.password)
    if user is None:
        register_login_attempt(identifier, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    register_login_attempt(identifier, success=True)
    roles = auth_service.get_user_role_names(db, user.id)
    token = create_access_token({"sub": str(user.id), "roles": roles})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = auth_service.get_user_role_names(db, current_user.id)
    return schemas.UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=roles,
    )
