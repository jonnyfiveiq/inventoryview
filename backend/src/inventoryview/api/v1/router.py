"""V1 API router aggregator."""

from fastapi import APIRouter

from inventoryview.api.v1 import auth, credentials, health, relationships, resources, setup

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(setup.router, prefix="/setup", tags=["setup"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(resources.router, prefix="/resources", tags=["resources"])
router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
