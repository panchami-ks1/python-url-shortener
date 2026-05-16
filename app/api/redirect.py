from datetime import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.cache.redis_client import get_redis
from app.core.logger import logger
from app.db.session import get_db
from app.services.url_service import get_url_by_code

router = APIRouter(tags=["redirect"])

@router.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)):
    # 1. Check Redis Cache
    cache_key = f"url:{short_code}"
    cached_url = redis_client.get(cache_key)
    
    if cached_url:
        logger.info(f"Cache HIT for short_code: {short_code}")
        return RedirectResponse(url=cached_url, status_code=307)
        
    # 2. Fallback to Database
    logger.info(f"Cache MISS for short_code: {short_code}. Fetching from DB.")
    db_url = get_url_by_code(db, short_code)
    if not db_url or not db_url.is_active:
        logger.warning(f"Redirect failed: URL '{short_code}' not found or inactive.")
        raise HTTPException(status_code=404, detail="URL not found or inactive")
        
    if db_url.expires_at and db_url.expires_at < datetime.utcnow():
        logger.warning(f"Redirect failed: URL '{short_code}' has expired.")
        raise HTTPException(status_code=410, detail="URL has expired")
        
    # 3. Save to cache for future requests (max 24 hours TTL)
    ttl = 86400
    if db_url.expires_at:
        time_left = int((db_url.expires_at - datetime.utcnow()).total_seconds())
        ttl = min(ttl, max(1, time_left))
        
    redis_client.setex(cache_key, ttl, db_url.original_url)
    
    # 4. Redirect
    return RedirectResponse(url=db_url.original_url, status_code=307)
