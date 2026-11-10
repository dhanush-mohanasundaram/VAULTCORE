from app import models
from app.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_roles(db: Session, user_id: int):
    return (
        db.query(models.Role.name)
        .join(models.UserRole, models.Role.id == models.UserRole.role_id)
        .filter(models.UserRole.user_id == user_id)
        .all()
    )


def register(db: Session, data: schemas.UserRegister):
    if get_user_by_email(db, data.email):
        return None
    user = models.User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.flush()
    customer_role = db.query(models.Role).filter(models.Role.name == "customer").first()
    if customer_role:
        db.add(models.UserRole(user_id=user.id, role_id=customer_role.id))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_role_names(db, user_id: int):
    return [
        r[0]
        for r in (
            db.query(models.Role.name)
            .join(models.UserRole, models.Role.id == models.UserRole.role_id)
            .filter(models.UserRole.user_id == user_id)
            .all()
        )
    ]

