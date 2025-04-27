from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: int):
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user