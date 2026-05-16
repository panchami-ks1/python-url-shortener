from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.models import User


class UserCreate(BaseModel):
    email: EmailStr
    password: str

def register_user(db: Session, user_in: UserCreate) -> User:
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        logger.warning(f"Registration failed: Email '{user_in.email}' already exists.")
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.email}")
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {email}")
        return None
        
    logger.info(f"User logged in successfully: {email}")
    return user

def create_tokens_for_user(db: Session, user_id: str):
    access_token = create_access_token(subject=user_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
