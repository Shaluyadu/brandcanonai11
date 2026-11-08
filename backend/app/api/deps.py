from datetime import datetime, timezone
from typing import Generator, List, Optional
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token, hash_session_token
from app.core.exceptions import AuthenticationError, PermissionDeniedError, TenantViolationError, NotFoundError
from app.models.user import User, Membership, UserSession, RoleEnum
from app.models.organisation import Organisation
from app.models.audit import AuditLog

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate session credentials from either:
    1. HTTP Authorization Bearer token header
    2. HttpOnly cookie 'brandcanon_session'
    Validates opaque session token against user_sessions table with SHA-256 hash, or validates JWT.
    """
    raw_token = None
    if auth_header and auth_header.credentials:
        raw_token = auth_header.credentials
    else:
        # Check cookie
        raw_token = request.cookies.get("brandcanon_session")

    if not raw_token:
        raise AuthenticationError("Authentication credentials not provided")

    # 1. Check if token is an opaque session token
    if raw_token.startswith("bcs_"):
        token_hash = hash_session_token(raw_token)
        now = datetime.now(timezone.utc)

        session_record = db.query(UserSession).filter(
            UserSession.session_token == token_hash,
            UserSession.is_revoked == False,
            UserSession.expires_at > now
        ).first()

        if not session_record:
            raise AuthenticationError("Session token is invalid or has expired")

        user = db.query(User).filter(User.id == session_record.user_id, User.is_active == True).first()
        if not user:
            raise AuthenticationError("Associated user account is deactivated or deleted")

        # Attach active session id to request state for revocation on logout
        request.state.session_id = session_record.id
        request.state.raw_token = raw_token
        return user

    # 2. Check if token is JWT
    payload = decode_access_token(raw_token)
    if not payload:
        raise AuthenticationError("Invalid or expired session token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Malformed token payload")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise AuthenticationError("User not found or account deactivated")

    request.state.session_id = None
    request.state.raw_token = raw_token
    return user


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    x_organisation_id: Optional[str] = Header(None, alias="X-Organisation-Id"),
    db: Session = Depends(get_db)
) -> Organisation:
    """
    Resolve active organisation tenant for the authenticated user.
    SECURITY RULE: Never trust the X-Organisation-Id header without verifying that the
    authenticated user is actually a member of that organisation.
    """
    if x_organisation_id:
        membership = db.query(Membership).filter(
            Membership.user_id == current_user.id,
            Membership.organisation_id == x_organisation_id
        ).first()

        if not membership:
            raise TenantViolationError(f"Access to requested organisation workspace '{x_organisation_id}' is forbidden")

        org = db.query(Organisation).filter(
            Organisation.id == x_organisation_id,
            Organisation.is_active == True
        ).first()

        if not org:
            raise NotFoundError("Requested organisation workspace not found or inactive")
        return org

    # Default to first active membership
    membership = db.query(Membership).filter(
        Membership.user_id == current_user.id
    ).order_by(Membership.is_default.desc(), Membership.created_at.asc()).first()

    if not membership:
        raise TenantViolationError("User is not associated with any active organisation workspace")

    org = db.query(Organisation).filter(
        Organisation.id == membership.organisation_id,
        Organisation.is_active == True
    ).first()

    if not org:
        raise NotFoundError("Associated organisation workspace not found")

    return org


def get_current_membership(
    current_user: User = Depends(get_current_user),
    current_tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Membership:
    """Return the user's membership and assigned role within the current active tenant."""
    membership = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.organisation_id == current_tenant.id
    ).first()

    if not membership:
        raise TenantViolationError("Membership record not found in active organisation")

    return membership


def require_role(allowed_roles: List[RoleEnum]):
    """Role-based access control dependency factory."""
    def role_checker(membership: Membership = Depends(get_current_membership)) -> Membership:
        allowed_values = [r.value if isinstance(r, RoleEnum) else r for r in allowed_roles]
        if membership.role not in allowed_values:
            raise PermissionDeniedError(
                f"Role '{membership.role}' lacks permission. Required one of: {allowed_values}"
            )
        return membership
    return role_checker


def record_audit_log(
    db: Session,
    organisation_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> AuditLog:
    """Record an immutable audit log entry within an active database transaction."""
    log_entry = AuditLog(
        organisation_id=organisation_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {}
    )
    db.add(log_entry)
    db.flush()
    return log_entry
