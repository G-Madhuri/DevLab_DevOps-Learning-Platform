from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import user_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of the currently logged-in user.
    """
    streak = user_service.calculate_streak(db, current_user.id)
    user_res = UserResponse.model_validate(current_user)
    user_res.streak = streak
    return user_res


@router.put("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update profile details (name/password) for the logged-in user.
    """
    updated_user = user_service.update_user_profile(db, current_user=current_user, user_update=user_update)
    streak = user_service.calculate_streak(db, updated_user.id)
    user_res = UserResponse.model_validate(updated_user)
    user_res.streak = streak
    return user_res
