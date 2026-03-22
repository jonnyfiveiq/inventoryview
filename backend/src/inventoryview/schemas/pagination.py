"""Cursor-based pagination schemas and helpers."""

import base64
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class PaginationInfo(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False
    page_size: int = DEFAULT_PAGE_SIZE


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationInfo


def encode_cursor(sort_value: Any, item_id: str) -> str:
    """Encode a cursor from sort value and item ID."""
    payload = json.dumps({"s": str(sort_value), "id": item_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, str]:
    """Decode a cursor into (sort_value, item_id). Raises ValueError on invalid cursor."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return payload["s"], payload["id"]
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid pagination cursor: {cursor}") from e


def clamp_page_size(page_size: int | None) -> int:
    """Clamp page_size to valid range."""
    if page_size is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(page_size, MAX_PAGE_SIZE))


class PaginationParams(BaseModel):
    """Common pagination query parameters."""

    cursor: str | None = Field(None, description="Pagination cursor")
    page_size: int = Field(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page")
