"""Bearer token authentication middleware."""

import logging
from datetime import UTC, datetime

import jwt
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from inventoryview.database import get_pool
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.services.auth import ALGORITHM, check_revoked

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI dependency that validates the bearer token.

    Returns the decoded JWT payload on success.
    Raises HTTPException-like responses for auth failures.
    """
    if credentials is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail=error_response(
                ErrorCode.UNAUTHORIZED, "Missing authentication token"
            ),
        )

    token = credentials.credentials
    settings = request.app.state.settings

    # Decode and validate JWT
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail=error_response(ErrorCode.UNAUTHORIZED, "Token has expired"),
        )
    except jwt.PyJWTError as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail=error_response(ErrorCode.UNAUTHORIZED, f"Invalid token: {e}"),
        )

    # Check revocation
    jti = payload.get("jti")
    if jti and await check_revoked(get_pool(), jti):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail=error_response(ErrorCode.UNAUTHORIZED, "Token has been revoked"),
        )

    return payload
