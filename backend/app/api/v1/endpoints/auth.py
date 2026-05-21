from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.core import status_codes
from app.core.exceptions import ConflictError
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status_codes.HTTP_CREATED,
    responses=status_codes.REGISTER_ERROR_RESPONSES,
)
def register(payload: RegisterRequest, db: DbSession) -> UserRead:
    service = AuthService(UserRepository(db))
    try:
        return service.register(payload)
    except ConflictError as exc:
        raise HTTPException(
            status_code=status_codes.HTTP_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=Token,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.LOGIN_ERROR_RESPONSES,
)
def login(payload: LoginRequest, db: DbSession) -> Token:
    service = AuthService(UserRepository(db))
    user = service.authenticate(str(payload.email), payload.password)
    if user is None:
        raise HTTPException(
            status_code=status_codes.HTTP_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return service.create_token_for_user(user)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status_codes.HTTP_OK,
    responses=status_codes.AUTHENTICATION_ERROR_RESPONSES,
)
def read_current_user(current_user: CurrentUser) -> UserRead:
    return current_user
