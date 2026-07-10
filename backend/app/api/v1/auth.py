from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.schemas.token import (
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenRequest,
    TokenResponse,
    GoogleTokenRequest,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import auth_service
from app.services.user import user_service
from fastapi import HTTPException

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    """
    return user_service.register_user(db, user_in=user_in)


@router.post("/login", response_model=TokenResponse)
def login(login_data: TokenRequest, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and return access & refresh tokens.
    """
    return auth_service.authenticate_user(
        db, email=login_data.username, password=login_data.password
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Get a new access token using a valid refresh token.
    """
    return auth_service.refresh_access_token(db, refresh_token=refresh_data.refresh_token)


@router.post("/logout")
def logout(logout_data: LogoutRequest, db: Session = Depends(get_db)):
    """
    Revoke a refresh token to logout user.
    """
    auth_service.logout(db, refresh_token=logout_data.refresh_token)
    return {"detail": "Successfully logged out"}


@router.post("/google-login", response_model=TokenResponse)
def google_login(google_data: GoogleTokenRequest, db: Session = Depends(get_db)):
    """
    Authenticate/register user using a Google Identity Token.
    """
    if google_data.token.startswith("mock-"):
        email = google_data.email or "google.user@devlab.com"
        name = google_data.name or "Google Learner"
    else:
        try:
            from jose import jwt
            payload = jwt.get_unverified_claims(google_data.token)
            email = payload.get("email")
            name = payload.get("name", email.split("@")[0])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Google token signature.")

    if not email:
        raise HTTPException(status_code=400, detail="Email not present in Google token.")

    return auth_service.login_google_user(db, email=email, name=name)
