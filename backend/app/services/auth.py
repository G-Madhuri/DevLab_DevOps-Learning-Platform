from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, verify_token
from app.models.token import RefreshToken
from app.models.user import User
from app.repositories.token import token_repository
from app.repositories.user import user_repository
from app.schemas.token import RefreshTokenResponse, TokenResponse


class AuthService:
    def authenticate_user(self, db: Session, email: str, password: str) -> TokenResponse:
        """
        Authenticate user credentials and issue fresh tokens.
        """
        user = user_repository.get_by_email(db, email=email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate tokens
        access_token = create_access_token(subject=user.id)
        refresh_token_str = create_refresh_token(subject=user.id)

        # Persist refresh token in database
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        token_data = {
            "user_id": user.id,
            "token": refresh_token_str,
            "expires_at": expires_at,
            "is_revoked": False,
        }
        token_repository.create(db, obj_in_data=token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            user=user,
        )

    def refresh_access_token(self, db: Session, refresh_token: str) -> RefreshTokenResponse:
        """
        Rotates the refresh token and issues a new access token if the provided token is valid.
        """
        user_id_str = verify_token(refresh_token, token_type="refresh")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        # Retrieve the token record from DB
        db_token = token_repository.get_by_token(db, token=refresh_token)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked or expired.",
            )

        # Safe timezone check for SQLite compatibility (converts naive datetime to aware)
        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if db_token.is_revoked or expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked or expired.",
            )

        # Rotate refresh token: Revoke old token
        db_token.is_revoked = True
        db.add(db_token)

        # Issue new tokens
        user = user_repository.get(db, id=db_token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        new_access_token = create_access_token(subject=user.id)
        new_refresh_token_str = create_refresh_token(subject=user.id)

        # Save new refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_token_data = {
            "user_id": user.id,
            "token": new_refresh_token_str,
            "expires_at": expires_at,
            "is_revoked": False,
        }
        token_repository.create(db, obj_in_data=new_token_data)
        db.commit()

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token_str,
        )

    def logout(self, db: Session, refresh_token: str) -> None:
        """
        Revokes the refresh token, logging out the user.
        """
        success = token_repository.revoke_token(db, token=refresh_token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token.",
            )


auth_service = AuthService()
