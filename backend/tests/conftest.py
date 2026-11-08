import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.core.security import hash_password, generate_session_token, hash_session_token
from app.models.organisation import Organisation, OrganisationSettings
from app.models.user import User, Membership, UserSession, RoleEnum
from app.models.audit import AuditLog
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_data(db_session):
    """Seed test fixtures: Org 1 (NovaTech) with Admin, Manager, Creator, Reviewer, and Org 2 (AcmeCorp)."""
    # Org 1: NovaTech
    org1 = Organisation(
        name="NovaTech",
        slug="novatech-test",
        industry="Technology",
        domain="novatech.io",
        is_active=True
    )
    db_session.add(org1)
    db_session.flush()

    settings1 = OrganisationSettings(
        organisation_id=org1.id,
        enforce_brand_voice=True,
        strict_mode=False,
        custom_metadata={}
    )
    db_session.add(settings1)

    hashed_pwd = hash_password("Password123!")

    # Users in Org 1
    admin_user = User(
        email="admin@test.io",
        hashed_password=hashed_pwd,
        full_name="Admin User",
        is_active=True,
        is_verified=True
    )
    db_session.add(admin_user)

    brand_manager_user = User(
        email="brand@test.io",
        hashed_password=hashed_pwd,
        full_name="Brand Manager User",
        is_active=True,
        is_verified=True
    )
    db_session.add(brand_manager_user)

    creator_user = User(
        email="creator@test.io",
        hashed_password=hashed_pwd,
        full_name="Creator User",
        is_active=True,
        is_verified=True
    )
    db_session.add(creator_user)

    reviewer_user = User(
        email="reviewer@test.io",
        hashed_password=hashed_pwd,
        full_name="Reviewer User",
        is_active=True,
        is_verified=True
    )
    db_session.add(reviewer_user)
    db_session.flush()

    # Memberships in Org 1
    m_admin = Membership(organisation_id=org1.id, user_id=admin_user.id, role=RoleEnum.ADMIN.value, is_default=True)
    m_manager = Membership(organisation_id=org1.id, user_id=brand_manager_user.id, role=RoleEnum.BRAND_MANAGER.value, is_default=True)
    m_creator = Membership(organisation_id=org1.id, user_id=creator_user.id, role=RoleEnum.CREATOR.value, is_default=True)
    m_reviewer = Membership(organisation_id=org1.id, user_id=reviewer_user.id, role=RoleEnum.REVIEWER.value, is_default=True)
    db_session.add_all([m_admin, m_manager, m_creator, m_reviewer])

    # Initial audit log for Org 1
    audit1 = AuditLog(
        organisation_id=org1.id,
        user_id=admin_user.id,
        event_type="WORKSPACE_CREATED",
        entity_type="ORGANISATION",
        entity_id=org1.id,
        metadata_json={"name": org1.name}
    )
    db_session.add(audit1)

    # Org 2: AcmeCorp (for tenant isolation tests)
    org2 = Organisation(
        name="AcmeCorp",
        slug="acme-test",
        industry="Retail",
        domain="acme.com",
        is_active=True
    )
    db_session.add(org2)
    db_session.flush()

    org2_user = User(
        email="acme_user@acme.com",
        hashed_password=hashed_pwd,
        full_name="Acme User",
        is_active=True,
        is_verified=True
    )
    db_session.add(org2_user)
    db_session.flush()

    m_org2 = Membership(organisation_id=org2.id, user_id=org2_user.id, role=RoleEnum.ADMIN.value, is_default=True)
    db_session.add(m_org2)

    # Initial audit log for Org 2
    audit2 = AuditLog(
        organisation_id=org2.id,
        user_id=org2_user.id,
        event_type="WORKSPACE_CREATED",
        entity_type="ORGANISATION",
        entity_id=org2.id,
        metadata_json={"name": org2.name}
    )
    db_session.add(audit2)

    # Generate Opaque Sessions for test users
    users = [admin_user, brand_manager_user, creator_user, reviewer_user, org2_user]
    tokens = {}
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    for u in users:
        org_id = org2.id if u == org2_user else org1.id
        raw_token = generate_session_token()
        session = UserSession(
            user_id=u.id,
            organisation_id=org_id,
            session_token=hash_session_token(raw_token),
            is_revoked=False,
            expires_at=expires_at
        )
        db_session.add(session)
        tokens[u.email] = raw_token

    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin_user": admin_user,
        "brand_manager_user": brand_manager_user,
        "creator_user": creator_user,
        "reviewer_user": reviewer_user,
        "org2_user": org2_user,
        "admin_token": tokens["admin@test.io"],
        "manager_token": tokens["brand@test.io"],
        "creator_token": tokens["creator@test.io"],
        "reviewer_token": tokens["reviewer@test.io"],
        "org2_token": tokens["acme_user@acme.com"]
    }
