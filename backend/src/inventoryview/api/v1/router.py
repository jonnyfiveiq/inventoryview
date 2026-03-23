"""V1 API router aggregator."""

from fastapi import APIRouter

from inventoryview.api.v1 import auth, automations, correlations, credentials, drift, health, playlists, relationships, resources, setup, usage

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(setup.router, prefix="/setup", tags=["setup"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(resources.router, prefix="/resources", tags=["resources"])
router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
router.include_router(drift.router, prefix="/drift", tags=["drift"])
router.include_router(correlations.router, prefix="/correlations", tags=["correlations"])
router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
router.include_router(automations.router, prefix="/automations", tags=["automations"])
router.include_router(usage.router, prefix="/usage", tags=["usage"])
