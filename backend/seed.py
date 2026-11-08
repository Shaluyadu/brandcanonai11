import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.organisation import Organisation, OrganisationSettings
from app.models.user import User, Membership, RoleEnum
from app.models.audit import AuditLog
from app.models.brand_knowledge import (
    BrandProfile,
    ApprovedFact,
    TerminologyRule,
    KnowledgeApproval,
    ApprovalStatus
)

DEFAULT_PASSWORD = "NovaTech@2026!"


def seed_database():
    """Seed the initial NovaTech organization and role accounts for demonstration."""
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if NovaTech already exists
        existing_org = db.query(Organisation).filter(Organisation.slug == "novatech").first()
        if existing_org:
            print("NovaTech organization already exists. Ensuring Phase 2 knowledge hub baseline is seeded...")
            org = existing_org
        else:
            print("Seeding NovaTech organization...")
            org = Organisation(
                name="NovaTech Solutions",
                slug="novatech",
                industry="Enterprise Technology & Cloud AI",
                domain="novatech.io",
                is_active=True
            )
            db.add(org)
            db.flush()

            settings = OrganisationSettings(
                organisation_id=org.id,
                enforce_brand_voice=True,
                strict_mode=False,
                custom_metadata={
                    "tagline": "Next-Gen Enterprise Infrastructure",
                    "founded_year": 2021
                }
            )
            db.add(settings)
            db.flush()

            # Seed Users for all 4 RBAC Roles with Argon2id hash
            users_data = [
                {
                    "email": "admin@novatech.io",
                    "full_name": "NovaTech Workspace Admin",
                    "role": RoleEnum.ADMIN.value
                },
                {
                    "email": "brand@novatech.io",
                    "full_name": "Sarah Chen (Brand Manager)",
                    "role": RoleEnum.BRAND_MANAGER.value
                },
                {
                    "email": "creator@novatech.io",
                    "full_name": "Alex Rivera (Content Creator)",
                    "role": RoleEnum.CREATOR.value
                },
                {
                    "email": "reviewer@novatech.io",
                    "full_name": "Marcus Vance (Compliance Reviewer)",
                    "role": RoleEnum.REVIEWER.value
                }
            ]

            hashed_pwd = hash_password(DEFAULT_PASSWORD)

            for u_data in users_data:
                user = User(
                    email=u_data["email"],
                    hashed_password=hashed_pwd,
                    full_name=u_data["full_name"],
                    is_active=True,
                    is_verified=True
                )
                db.add(user)
                db.flush()

                membership = Membership(
                    organisation_id=org.id,
                    user_id=user.id,
                    role=u_data["role"],
                    is_default=True
                )
                db.add(membership)
                db.flush()

                audit = AuditLog(
                    organisation_id=org.id,
                    user_id=user.id,
                    event_type="USER_SEEDED",
                    entity_type="USER",
                    entity_id=user.id,
                    metadata_json={"email": user.email, "role": u_data["role"]}
                )
                db.add(audit)

        # Seed Brand Profile for NovaTech if not present
        existing_profile = db.query(BrandProfile).filter(BrandProfile.organisation_id == org.id).first()
        brand_manager_user = db.query(User).filter(User.email == "brand@novatech.io").first()

        if not existing_profile:
            profile = BrandProfile(
                organisation_id=org.id,
                brand_name="NovaTech Solutions",
                industry="Enterprise Technology & Cloud AI",
                domain="novatech.io",
                description="Leading provider of mission-critical enterprise cloud compliance and brand governance platforms.",
                brand_voice="Authoritative, transparent, objective, and precise. Avoid hype, unverified claims, or corporate jargon.",
                target_audience="Enterprise Chief Marketing Officers, Compliance Directors, and In-house Legal Counsel.",
                publishing_channels=["Website", "LinkedIn", "Press Releases", "Developer Blog"],
                applicable_regions=["Global", "North America", "Europe"]
            )
            db.add(profile)
            db.flush()
            print("  - Brand Profile seeded.")

        # Seed Initial Approved Facts if not present
        existing_facts_count = db.query(ApprovedFact).filter(ApprovedFact.organisation_id == org.id).count()
        if existing_facts_count == 0:
            facts_data = [
                {
                    "title": "99.99% Cloud Service Level Agreement (SLA)",
                    "claim_text": "NovaTech guarantees 99.99% monthly availability for all Enterprise Cloud tier deployments.",
                    "category": "PERFORMANCE",
                    "evidence_quote": "Master Service Agreement Section 4.2 guaranteed uptime.",
                    "source_page": 12,
                    "applicable_region": "GLOBAL"
                },
                {
                    "title": "SOC 2 Type II and ISO 27001 Certified",
                    "claim_text": "NovaTech infrastructure is fully SOC 2 Type II and ISO 27001 certified with continuous third-party surveillance audits.",
                    "category": "COMPLIANCE",
                    "evidence_quote": "Annual Ernst & Young SOC 2 Type II audit report issued October 2026.",
                    "source_page": 4,
                    "applicable_region": "GLOBAL"
                }
            ]

            for f_data in facts_data:
                fact = ApprovedFact(
                    organisation_id=org.id,
                    title=f_data["title"],
                    claim_text=f_data["claim_text"],
                    category=f_data["category"],
                    evidence_quote=f_data["evidence_quote"],
                    source_page=f_data["source_page"],
                    applicable_region=f_data["applicable_region"],
                    applicable_audience="ALL",
                    status=ApprovalStatus.APPROVED.value,
                    created_by=brand_manager_user.id if brand_manager_user else None,
                    approved_by=brand_manager_user.id if brand_manager_user else None,
                    approved_at=org.created_at
                )
                db.add(fact)
                db.flush()

                appr = KnowledgeApproval(
                    organisation_id=org.id,
                    entity_type="FACT",
                    entity_id=fact.id,
                    decision="APPROVED",
                    reviewer_id=brand_manager_user.id if brand_manager_user else org.id,
                    reason="Initial baseline approved knowledge"
                )
                db.add(appr)
                print(f"  - Approved Fact seeded: {fact.title}")

        # Seed Initial Terminology Rules if not present
        existing_terms_count = db.query(TerminologyRule).filter(TerminologyRule.organisation_id == org.id).count()
        if existing_terms_count == 0:
            terminology_data = [
                {
                    "prohibited": "cheap",
                    "preferred": "cost-effective",
                    "match_type": "WHOLE_WORD",
                    "severity": "HIGH",
                    "description": "Never use 'cheap' when referring to NovaTech pricing."
                },
                {
                    "prohibited": "synergy",
                    "preferred": "coordination",
                    "match_type": "WHOLE_WORD",
                    "severity": "MEDIUM",
                    "description": "Avoid vague buzzwords in official documentation."
                },
                {
                    "prohibited": "foolproof",
                    "preferred": "robust and validated",
                    "match_type": "WHOLE_WORD",
                    "severity": "HIGH",
                    "description": "Avoid absolute claims that cannot be legally indemnified."
                }
            ]

            for t_data in terminology_data:
                term = TerminologyRule(
                    organisation_id=org.id,
                    prohibited_term=t_data["prohibited"],
                    preferred_term=t_data["preferred"],
                    match_type=t_data["match_type"],
                    severity=t_data["severity"],
                    case_sensitive=False,
                    category="BRAND_IDENTITY",
                    description=t_data["description"],
                    status="ACTIVE",
                    created_by=brand_manager_user.id if brand_manager_user else None,
                    approved_by=brand_manager_user.id if brand_manager_user else None,
                    approved_at=org.created_at
                )
                db.add(term)
                db.flush()

                appr = KnowledgeApproval(
                    organisation_id=org.id,
                    entity_type="TERMINOLOGY_RULE",
                    entity_id=term.id,
                    decision="APPROVED",
                    reviewer_id=brand_manager_user.id if brand_manager_user else org.id,
                    reason="Standard brand voice vocabulary rules"
                )
                db.add(appr)
                print(f"  - Terminology Rule seeded: '{term.prohibited_term}' -> '{term.preferred_term}'")

        db.commit()
        print("NovaTech organization and Brand Knowledge Hub baseline seeded successfully.")
        demo_accounts = [
            ("ADMIN", "admin@novatech.io"),
            ("BRAND_MANAGER", "brand@novatech.io"),
            ("CREATOR", "creator@novatech.io"),
            ("REVIEWER", "reviewer@novatech.io"),
        ]
        for role, email in demo_accounts:
            print(f"  - {role:<15}: {email} (Password: {DEFAULT_PASSWORD})")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
