"""Setup endpoints."""

from argon2 import PasswordHasher
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.schemas.auth import (
    SetupInitRequest,
    SetupInitResponse,
    SetupStatusResponse,
)
from inventoryview.schemas.errors import ErrorCode, error_response

router = APIRouter()
ph = PasswordHasher()


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status() -> SetupStatusResponse:
    """Check whether initial setup has been completed."""
    async with get_pool().connection() as conn:
        result = await conn.execute(
            "SELECT EXISTS(SELECT 1 FROM administrators WHERE setup_complete = true) AS complete"
        )
        row = await result.fetchone()
        setup_complete = row["complete"] if row else False

    return SetupStatusResponse(setup_complete=setup_complete)


@router.post("/init", response_model=SetupInitResponse, status_code=201)
async def setup_init(body: SetupInitRequest) -> SetupInitResponse | JSONResponse:
    """Create the initial administrator account.

    Only succeeds when no administrator rows exist yet.
    """
    async with get_pool().connection() as conn:
        result = await conn.execute("SELECT COUNT(*) AS cnt FROM administrators")
        row = await result.fetchone()
        if row and row["cnt"] > 0:
            return JSONResponse(
                status_code=409,
                content=error_response(
                    ErrorCode.CONFLICT,
                    "Setup has already been completed",
                ),
            )

        password_hash = ph.hash(body.password)
        await conn.execute(
            "INSERT INTO administrators (username, password_hash, setup_complete) VALUES (%s, %s, %s)",
            ["admin", password_hash, True],
        )

    return SetupInitResponse(
        message="Administrator account created successfully",
        username="admin",
    )
