"""Relationship edge model."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EdgeType(StrEnum):
    DEPENDS_ON = "DEPENDS_ON"
    DEPENDED_ON_BY = "DEPENDED_ON_BY"
    HOSTED_ON = "HOSTED_ON"
    HOSTS = "HOSTS"
    MEMBER_OF = "MEMBER_OF"
    CONTAINS = "CONTAINS"
    CONNECTED_TO = "CONNECTED_TO"
    ATTACHED_TO = "ATTACHED_TO"
    ATTACHED_FROM = "ATTACHED_FROM"
    MANAGES = "MANAGES"
    MANAGED_BY = "MANAGED_BY"
    ROUTES_TO = "ROUTES_TO"
    ROUTED_FROM = "ROUTED_FROM"
    PEERS_WITH = "PEERS_WITH"


class Relationship(BaseModel):
    """A directed edge between two resource nodes."""

    source_uid: str
    target_uid: str
    type: EdgeType
    source_collector: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    established_at: datetime
    last_confirmed: datetime
    inference_method: str | None = None
    metadata: dict | None = None
