import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, urls, redirect
from app.core.config import settings
from app.core.logger import logger

description = """
URL Shortener Service API helps you manage and track shortened URLs. 🚀

## Authentication
You can **register** and **login** to obtain a JWT token. This token must be passed in the `Authorization` header to create or manage your URLs.

## URLs
You will be able to:
* **Create** new short URLs (with optional custom aliases and expiration dates).
* **List** all your generated URLs.
* **Delete** your URLs.

## Redirection
* Redirection is lightning fast, utilizing a **Redis Cache** before falling back to the database.
"""

tags_metadata = [
    {
        "name": "auth",
        "description": "Operations with users. Register and login to get your JWT access token.",
    },
    {
        "name": "urls",
        "description": "Manage your short URLs. Requires authentication.",
    },
    {
        "name": "redirect",
        "description": "Public endpoints for redirecting short codes to their original URLs.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - {process_time:.2f}ms")
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {request.method} {request.url.path} - {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Include routers
app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(redirect.router)