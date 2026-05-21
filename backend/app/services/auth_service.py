from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, Token
from app.services.starter_data_service import StarterDataService


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def register(self, payload: RegisterRequest) -> User:
        email = str(payload.email).lower()
        nickname = payload.nickname.strip()

        if self.users.get_by_email(email) is not None:
            raise ConflictError("A user with this email already exists.")
        if self.users.get_by_nickname(nickname) is not None:
            raise ConflictError("A user with this nickname already exists.")

        user = User(
            nickname=nickname,
            email=email,
            password_hash=get_password_hash(payload.password),
        )
        try:
            self.users.add(user)
            StarterDataService(self.users.db).seed_for_new_owner(owner_id=user.id)
            self.users.db.commit()
            self.users.db.refresh(user)
        except IntegrityError as exc:
            self.users.db.rollback()
            raise ConflictError(
                "A user with this email or nickname already exists."
            ) from exc
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def create_token_for_user(self, user: User) -> Token:
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value},
        )
        return Token(access_token=access_token)

    def hash_password(self, password: str) -> str:
        return get_password_hash(password)
