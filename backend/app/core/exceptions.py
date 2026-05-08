class AppError(Exception):
    """Base application error for service-layer failures."""


class NotFoundError(AppError):
    """Raised when a requested domain object does not exist."""


class BusinessRuleError(AppError):
    """Raised when a domain invariant would be violated."""
