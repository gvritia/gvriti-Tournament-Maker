class AppError(Exception):
    """Base application error for service-layer failures."""


class NotFoundError(AppError):
    """Raised when a requested domain object does not exist."""


class ConflictError(AppError):
    """Raised when a unique or state conflict prevents an operation."""


class BusinessRuleError(AppError):
    """Raised when a domain invariant would be violated."""
