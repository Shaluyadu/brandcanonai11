from typing import Any, Optional
from fastapi import HTTPException, status


class BrandCanonException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details
            }
        )


class AuthenticationError(BrandCanonException):
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message
        )


class PermissionDeniedError(BrandCanonException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message
        )


class TenantViolationError(BrandCanonException):
    def __init__(self, message: str = "Access to requested organisation workspace is forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_ACCESS_FORBIDDEN",
            message=message
        )


class NotFoundError(BrandCanonException):
    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message
        )


class ConflictError(BrandCanonException):
    def __init__(self, message: str = "A resource with these details already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=message
        )


class ValidationError(BrandCanonException):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )

