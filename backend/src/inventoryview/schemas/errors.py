"""Standardised error response schemas."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    error: "ErrorBody"


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    details: list[Any] = []


def error_response(code: ErrorCode, message: str, details: list[Any] | None = None) -> dict:
    """Build a standardised error response dict."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }
