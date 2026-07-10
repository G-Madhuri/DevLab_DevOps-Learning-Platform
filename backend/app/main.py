from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

import time
from app.core.redis import redis_client

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Only rate-limit API calls
    if request.url.path.startswith(settings.API_V1_STR) and not request.url.path.endswith("/ws"):
        client_ip = request.client.host if request.client else "127.0.0.1"
        # Key windows per minute
        minute_key = f"ratelimit:{client_ip}:{int(time.time() // 60)}"
        try:
            count = redis_client.incr(minute_key)
            if count == 1:
                redis_client.expire(minute_key, 60)
            
            # Limit rate to 100 requests per minute
            if count > 100:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Rate limit exceeded. Try again in a minute."},
                )
        except Exception as e:
            # Resilient fallback: log exception and proceed so Redis failures don't block access
            logger.error(f"Rate limiting failure: {e}")
            
    response = await call_next(request)
    return response

# Centralized validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error occurred on path {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Input validation failed."},
    )

# Global generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on path {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """
    Diagnostic root endpoint.
    """
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
    }
