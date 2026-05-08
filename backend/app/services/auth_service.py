from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def hash_password(self, password: str) -> str:
        return get_password_hash(password)
