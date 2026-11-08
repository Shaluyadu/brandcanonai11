"""Governance API router registration"""

from fastapi import APIRouter

router = APIRouter()

# Import sub-modules to register their endpoints onto the router
from . import dashboard, submissions, evidence  # noqa: F401, E402
