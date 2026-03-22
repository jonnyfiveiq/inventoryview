"""Authentication endpoints - login and token revocation."""

import logging
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.auth import LoginRequest, LoginResponse, TokenRevokeRequest
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.services.auth import create_token, decode_token, revoke_token

logger = logging.getLogger(__name__)
router = APIRouter()
ph = PasswordHasher()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    """Authenticate and receive a bearer token."""
    settings = request.app.state.settings
    pool = get_pool()

    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT id, password_hash FROM administrators WHERE username = %s AND setup_complete = true",
            [body.username],
        )
        row = await result.fetchone()

    if row is None:
        return JSONResponse(
            status_code=401,
            content=error_response(ErrorCode.UNAUTHORIZED, "Invalid credentials"),
        )

    try:
        ph.verify(row["password_hash"], body.password)
    except VerifyMismatchError:
        return JSONResponse(
            status_code=401,
            content=error_response(ErrorCode.UNAUTHORIZED, "Invalid credentials"),
        )

    # Generate JWT secret if not set
    if not settings.jwt_secret:
        import secrets

        settings.jwt_secret = secrets.token_urlsafe(32)

    token, expires_at = create_token(
        subject=str(row["id"]),
        secret=settings.jwt_secret,
        expiry_hours=settings.token_expiry_hours,
    )

    return LoginResponse(
        token=token,
        token_type="bearer",
        expires_at=expires_at,
    )


@router.post("/revoke")
async def revoke(body: TokenRevokeRequest, request: Request, _=Depends(require_auth)):
    """Revoke a bearer token."""
    settings = request.app.state.settings
    pool = get_pool()

    try:
        payload = decode_token(body.token, settings.jwt_secret)
    except Exception:
        return JSONResponse(
            status_code=400,
            content=error_response(ErrorCode.VALIDATION_ERROR, "Invalid token provided"),
        )

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=UTC)
        await revoke_token(pool, jti, expires_at)

    return {"message": "Token revoked successfully"}
