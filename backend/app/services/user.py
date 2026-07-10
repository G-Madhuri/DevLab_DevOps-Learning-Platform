from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def register_user(self, db: Session, user_in: UserCreate) -> User:
        """
        Registers a new user, checking if the email already exists and hashing the password.
        """
        existing_user = user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        user_data = {
            "name": user_in.name,
            "email": user_in.email,
            "password_hash": get_password_hash(user_in.password),
        }
        return user_repository.create(db, obj_in_data=user_data)

    def update_user_profile(
        self, db: Session, current_user: User, user_update: UserUpdate
    ) -> User:
        """
        Updates a user profile. Handles name updates and secure password rotation.
        """
        update_data = {}

        if user_update.name is not None:
            update_data["name"] = user_update.name

        # Handle password change
        if user_update.new_password is not None:
            if user_update.current_password is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to change password.",
                )
            if not verify_password(user_update.current_password, current_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect current password.",
                )
            update_data["password_hash"] = get_password_hash(user_update.new_password)

        if not update_data:
            return current_user

        return user_repository.update(db, db_obj=current_user, obj_in_data=update_data)


user_service = UserService()
