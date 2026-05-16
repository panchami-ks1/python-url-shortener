from datetime import datetime
from typing import List
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.services.url_service import create_short_url, URLCreate, get_user_urls, delete_user_url

router = APIRouter(prefix="/api/v1/urls", tags=["urls"])

class URLResponse(BaseModel):
    id: str
    short_code: str
    short_url: str
    original_url: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("", response_model=URLResponse)
def create_url(url_in: URLCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_url = create_short_url(db, url_in, current_user)
    
    return {
        "id": str(db_url.id),
        "short_code": db_url.short_code,
        "short_url": f"{settings.BASE_URL}/{db_url.short_code}",
        "original_url": db_url.original_url,
        "expires_at": db_url.expires_at,
        "created_at": db_url.created_at
    }

@router.get("", response_model=List[URLResponse])
def read_user_urls(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    urls = get_user_urls(db, str(current_user.id))
    result = []
    for u in urls:
        result.append({
            "id": str(u.id),
            "short_code": u.short_code,
            "short_url": f"{settings.BASE_URL}/{u.short_code}",
            "original_url": u.original_url,
            "expires_at": u.expires_at,
            "created_at": u.created_at
        })
    return result

@router.delete("/{url_id}")
def delete_url(url_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_user_url(db, url_id, current_user)
