"""Relationship request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from inventoryview.models.relationship import EdgeType


class RelationshipCreateRequest(BaseModel):
    source_uid: str
    target_uid: str
    type: EdgeType
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source_collector: str | None = None
    inference_method: str | None = None
    metadata: dict | None = None


class RelationshipResponse(BaseModel):
    source_uid: str
    target_uid: str
    type: str
    confidence: float
    source_collector: str | None = None
    established_at: datetime
    last_confirmed: datetime
    inference_method: str | None = None
    metadata: dict | None = None


class RelationshipDeleteRequest(BaseModel):
    source_uid: str
    target_uid: str
    type: EdgeType


class SubgraphNodeResponse(BaseModel):
    uid: str
    name: str
    category: str
    vendor: str


class SubgraphEdgeResponse(BaseModel):
    source_uid: str
    target_uid: str
    type: str
    confidence: float


class SubgraphResponse(BaseModel):
    nodes: list[SubgraphNodeResponse]
    edges: list[SubgraphEdgeResponse]
