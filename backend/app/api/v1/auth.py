import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    generate_session_token,
    hash_session_token,
    create_access_token
)
from app.core.rate_limit import auth_rate_limiter
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.api.deps import get_current_user, get_current_tenant, get_current_membership, record_audit_log
from app.models.user import User, Membership, UserSession, RoleEnum
from app.models.organisation import Organisation, OrganisationSettings
from app.schemas.common import APIResponse
from app.schemas.auth import UserRegister, UserLogin, UserOut, AuthResponse, MeResponse, OrganisationOut

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def set_auth_cookie(response: Response, token: str):
    """Set secure, HttpOnly, SameSite session cookie."""
    is_prod = settings.APP_ENV.lower() == "production"
    response.set_cookie(
        key="brandcanon_session",
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )


@router.post("/register", response_model=APIResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register a new user, create their organisation workspace, and establish an active session."""
    auth_rate_limiter.check(request, key_prefix="register")
    email_clean = payload.email.lower().strip()

    # Check existing user
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise ConflictError("An account with this email address already exists")

    # Generate workspace slug
    org_name = payload.organisation_name.strip() if payload.organisation_name else f"{payload.full_name.strip()}'s Workspace"
    base_slug = slugify(org_name)
    slug = base_slug
    counter = 1
    while db.query(Organisation).filter(Organisation.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create User with Argon2id password hash
    new_user = User(
        email=email_clean,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        is_active=True,
        # Default to False until email verification service is active
        is_verified=False
    )
    db.add(new_user)
    db.flush()

    # Create Organisation & Governance Settings
    new_org = Organisation(
        name=org_name,
        slug=slug,
        is_active=True
    )
    db.add(new_org)
    db.flush()

    org_settings = OrganisationSettings(
        organisation_id=new_org.id,
        enforce_brand_voice=True,
        strict_mode=False,
        custom_metadata={}
    )
    db.add(org_settings)
    db.flush()

    # Create Owner / Workspace Admin Membership
    membership = Membership(
        organisation_id=new_org.id,
        user_id=new_user.id,
        role=RoleEnum.ADMIN.value,
        is_default=True
    )
    db.add(membership)
    db.flush()

    # Create Opaque Session Record in Database
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session_record = UserSession(
        user_id=new_user.id,
        organisation_id=new_org.id,
        session_token=token_hash,
        is_revoked=False,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")[:500] if request.headers.get("user-agent") else None
    )
    db.add(session_record)
    db.flush()

    # Record Immutable Audit Events
    record_audit_log(
        db=db,
        organisation_id=new_org.id,
        user_id=new_user.id,
        event_type="AUTH_REGISTER",
        entity_type="USER",
        entity_id=new_user.id,
        metadata={"email": email_clean}
    )
    record_audit_log(
        db=db,
        organisation_id=new_org.id,
        user_id=new_user.id,
        event_type="WORKSPACE_CREATED",
        entity_type="ORGANISATION",
        entity_id=new_org.id,
        metadata={"name": org_name, "slug": slug}
    )

    db.commit()
    db.refresh(new_user)
    db.refresh(new_org)

    # Set HttpOnly Cookie
    set_auth_cookie(response, raw_token)

    return APIResponse(
        success=True,
        message="Account and organisation workspace created successfully",
        data=AuthResponse(
            access_token=raw_token,
            token_type="bearer",
            user=UserOut.model_validate(new_user),
            active_organisation=OrganisationOut.model_validate(new_org),
            current_role=membership.role
        )
    )


@router.post("/login", response_model=APIResponse[AuthResponse])
def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate credentials, create an active database session, and issue tokens."""
    auth_rate_limiter.check(request, key_prefix="login")
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("This user account has been disabled")

    # Find active memberships
    memberships = db.query(Membership).filter(
        Membership.user_id == user.id
    ).order_by(Membership.is_default.desc(), Membership.created_at.asc()).all()

    if not memberships:
        raise AuthenticationError("User is not associated with any active organisation")

    active_membership = memberships[0]
    org = db.query(Organisation).filter(
        Organisation.id == active_membership.organisation_id,
        Organisation.is_active == True
    ).first()

    if not org:
        raise NotFoundError("Active organisation workspace not found or inactive")

    # Create Opaque Session Record
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session_record = UserSession(
        user_id=user.id,
        organisation_id=org.id,
        session_token=token_hash,
        is_revoked=False,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")[:500] if request.headers.get("user-agent") else None
    )
    db.add(session_record)

    record_audit_log(
        db=db,
        organisation_id=org.id,
        user_id=user.id,
        event_type="AUTH_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        metadata={"email": user.email}
    )
    db.commit()

    # Set HttpOnly Cookie
    set_auth_cookie(response, raw_token)

    return APIResponse(
        success=True,
        message="Login successful",
        data=AuthResponse(
            access_token=raw_token,
            token_type="bearer",
            user=UserOut.model_validate(user),
            active_organisation=OrganisationOut.model_validate(org),
            current_role=active_membership.role
        )
    )


@router.get("/me", response_model=APIResponse[MeResponse])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    current_tenant: Organisation = Depends(get_current_tenant),
    current_membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Retrieve authenticated user details, active workspace role, and permitted organizations."""
    all_memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
    org_ids = [m.organisation_id for m in all_memberships]
    permitted_orgs = db.query(Organisation).filter(
        Organisation.id.in_(org_ids),
        Organisation.is_active == True
    ).all()

    return APIResponse(
        success=True,
        data=MeResponse(
            user=UserOut.model_validate(current_user),
            active_organisation=OrganisationOut.model_validate(current_tenant),
            current_role=current_membership.role,
            permitted_organisations=[OrganisationOut.model_validate(o) for o in permitted_orgs]
        )
    )


@router.post("/logout", response_model=APIResponse[dict])
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    current_tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Revoke active session token in database, remove cookie, and log audit event."""
    session_id = getattr(request.state, "session_id", None)
    raw_token = getattr(request.state, "raw_token", None)

    if session_id:
        db.query(UserSession).filter(UserSession.id == session_id).update({"is_revoked": True})
    elif raw_token and raw_token.startswith("bcs_"):
        token_hash = hash_session_token(raw_token)
        db.query(UserSession).filter(UserSession.session_token == token_hash).update({"is_revoked": True})

    record_audit_log(
        db=db,
        organisation_id=current_tenant.id,
        user_id=current_user.id,
        event_type="AUTH_LOGOUT",
        entity_type="USER",
        entity_id=current_user.id,
        metadata={"email": current_user.email}
    )
    db.commit()

    # Clear HttpOnly Cookie
    response.delete_cookie(key="brandcanon_session", path="/")

    return APIResponse(
        success=True,
        message="Session revoked and logged out successfully",
        data={"user_id": current_user.id}
    )
