from fastapi import APIRouter
from app.api.v1 import (
    auth,
    organisations,
    members,
    audit,
    brand_overview,
    brand_profile,
    brand_documents,
    brand_facts,
    brand_terminology,
    brand_approvals,
    governance,
    analytics,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
api_router.include_router(organisations.router, prefix="/organisations", tags=["Organisations & Workspace"])
api_router.include_router(members.router, prefix="/members", tags=["Members & Roles"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Trails"])

# Phase 2 — Brand Knowledge Hub
api_router.include_router(brand_overview.router, prefix="/brand", tags=["Brand Knowledge Hub"])
api_router.include_router(brand_profile.router, prefix="/brand", tags=["Brand Profile"])
api_router.include_router(brand_documents.router, prefix="/brand", tags=["Brand Documents"])
api_router.include_router(brand_facts.router, prefix="/brand", tags=["Brand Facts"])
api_router.include_router(brand_terminology.router, prefix="/brand", tags=["Brand Terminology"])
api_router.include_router(brand_approvals.router, prefix="/brand", tags=["Brand Knowledge Approvals"])

# Phase 5 — Governance & Review
api_router.include_router(governance.router, prefix="/governance", tags=["Governance Dashboard & Submissions"])

# Phase 6 — Analytics & Hardening
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Insights"])
