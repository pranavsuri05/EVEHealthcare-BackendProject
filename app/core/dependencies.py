from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import decode_token
from app.db.models import User
from app.core.exceptions import NotAuthenticated

security = HTTPBearer()


async def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT from request header"""
    token = credentials.credentials

    payload = decode_token(token)
    if not payload:
        raise NotAuthenticated()

    user_id = payload.get("sub")
    if not user_id:
        raise NotAuthenticated()

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise NotAuthenticated()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotAuthenticated()

    return user
