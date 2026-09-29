from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import UserAlreadyExists, InvalidCredentials
from app.core.logging import log_user_signup, log_auth_failure


class AuthService:
    @staticmethod
    def signup(email: str, password: str, db: Session) -> User:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            log_auth_failure(email, "duplicate_email")
            raise UserAlreadyExists()

        # Create new user
        hashed_password = hash_password(password)
        user = User(email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

        log_user_signup(email)
        return user

    @staticmethod
    def login(email: str, password: str, db: Session) -> tuple[User, str]:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            log_auth_failure(email, "user_not_found")
            raise InvalidCredentials()

        # Verify password
        if not verify_password(password, user.hashed_password):
            log_auth_failure(email, "invalid_password")
            raise InvalidCredentials()

        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        return user, access_token

    @staticmethod
    def get_user_from_token(user_id: int, db: Session) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        return user
