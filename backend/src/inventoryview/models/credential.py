"""Credential domain models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class CredentialType(StrEnum):
    AWS_KEY_PAIR = "aws_key_pair"
    AZURE_SERVICE_PRINCIPAL = "azure_service_principal"
    GCP_SERVICE_ACCOUNT = "gcp_service_account"
    VSPHERE = "vsphere"
    OPENSHIFT_KUBERNETES = "openshift_kubernetes"
    BEARER_TOKEN = "bearer_token"
    USERNAME_PASSWORD = "username_password"
    SSH_KEY = "ssh_key"


class Credential(BaseModel):
    """Credential metadata - never includes secret fields."""

    id: UUID
    name: str
    credential_type: CredentialType
    metadata: dict
    associated_collector: str | None = None
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None


class CredentialAuditEntry(BaseModel):
    """A single entry in the credential audit log."""

    id: UUID
    credential_id: UUID | None
    operation: str
    actor: str
    timestamp: datetime
    details: dict | None = None
