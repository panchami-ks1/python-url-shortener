import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models import URL, User


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=6, 
        description="Optional custom alias. Must be between 1 and 6 characters long."
    )
    expires_at: Optional[datetime] = None

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def create_short_url(db: Session, url_in: URLCreate, current_user: User) -> URL:
    # Check if custom alias is requested
    short_code = url_in.custom_alias
    if short_code:
        existing = db.query(URL).filter(URL.short_code == short_code).first()
        if existing:
            logger.warning(f"URL creation failed: Custom alias '{short_code}' already exists.")
            raise HTTPException(status_code=400, detail="Custom alias already exists.")
    else:
        # Generate a unique code
        while True:
            short_code = generate_short_code()
            if not db.query(URL).filter(URL.short_code == short_code).first():
                break

    # Validate URL to prevent SSRF and Open Redirect issues
    original_url_str = str(url_in.original_url)
    if "javascript:" in original_url_str.lower() or "localhost" in original_url_str.lower():
        logger.warning(f"URL creation blocked: Invalid scheme or host - {original_url_str}")
        raise HTTPException(status_code=400, detail="Invalid URL scheme or host.")

    if url_in.expires_at:
        now = datetime.now(url_in.expires_at.tzinfo) if url_in.expires_at.tzinfo else datetime.utcnow()
        if url_in.expires_at <= now:
            logger.warning(f"URL creation failed: Expiration date is in the past ({url_in.expires_at})")
            raise HTTPException(status_code=400, detail="Expiration date must be in the future.")

    expires_at = url_in.expires_at or (datetime.utcnow() + timedelta(hours=1))
    
    db_url = URL(
        user_id=current_user.id,
        original_url=original_url_str,
        short_code=short_code,
        expires_at=expires_at
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    logger.info(f"Created short URL '{short_code}' for user_id: {current_user.id}")
    return db_url

def get_url_by_code(db: Session, short_code: str) -> Optional[URL]:
    return db.query(URL).filter(URL.short_code == short_code).first()

def get_user_urls(db: Session, user_id: str):
    return db.query(URL).filter(URL.user_id == user_id).order_by(URL.expires_at.desc()).all()

def delete_user_url(db: Session, url_id: str, current_user: User):
    db_url = db.query(URL).filter(URL.id == url_id).first()
    if not db_url:
        logger.warning(f"URL deletion failed: URL ID '{url_id}' not found.")
        raise HTTPException(status_code=404, detail="URL not found")
    if db_url.user_id != current_user.id:
        logger.warning(f"URL deletion forbidden: User '{current_user.id}' attempted to delete URL owned by '{db_url.user_id}'.")
        raise HTTPException(status_code=403, detail="Not authorized to delete this URL")
    
    db.delete(db_url)
    db.commit()
    logger.info(f"Deleted short URL '{db_url.short_code}' for user_id: {current_user.id}")
    return {"detail": "URL deleted successfully"}
