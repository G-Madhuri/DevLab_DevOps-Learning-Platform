from fastapi import APIRouter
from app.api.v1 import auth, users, labs

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(labs.router, prefix="/labs", tags=["labs"])
