from fastapi import HTTPException

from app.core import status_codes
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError


def app_error_to_http_exception(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(
            status_code=status_codes.HTTP_NOT_FOUND,
            detail=str(error),
        )
    if isinstance(error, ConflictError):
        return HTTPException(
            status_code=status_codes.HTTP_CONFLICT,
            detail=str(error),
        )
    if isinstance(error, BusinessRuleError):
        return HTTPException(
            status_code=status_codes.HTTP_BAD_REQUEST,
            detail=str(error),
        )
    return HTTPException(
        status_code=status_codes.HTTP_BAD_REQUEST,
        detail="Application error.",
    )
