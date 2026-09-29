from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: UserSignupRequest, db: Session = Depends(get_db)):
    """
    User signup endpoint.

    Creates a new user with the provided email and password.
    Returns a JWT access token for subsequent authenticated requests.
    """
    user = AuthService.signup(request.email, request.password, db)
    access_token = AuthService.login(request.email, request.password, db)[1]
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint.

    Authenticates user with email and password.
    Returns a JWT access token for subsequent authenticated requests.
    """
    user, access_token = AuthService.login(request.email, request.password, db)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return current_user
