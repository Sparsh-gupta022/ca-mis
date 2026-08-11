"""
Pydantic schemas for the Client resource.

These mirror the Client fields exactly as defined in DATABASE_SPEC.md /
app/models/client.py and the response shape promised by API_SPEC.md.
No fields are added or renamed here.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    """Fields shared by create/update payloads."""

    name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=100)
    pan_gstin: str | None = Field(default=None, max_length=30)
    contact: str | None = Field(default=None, max_length=255)
    partner_in_charge: str | None = Field(default=None, max_length=255)


class ClientCreate(ClientBase):
    """Payload for POST /clients. name and entity_type are required."""


class ClientUpdate(BaseModel):
    """
    Payload for PUT /clients/{client_id}.

    All fields are optional so a client can be updated with a partial
    payload, but name/entity_type — if provided — still can't be blank.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    entity_type: str | None = Field(default=None, min_length=1, max_length=100)
    pan_gstin: str | None = Field(default=None, max_length=30)
    contact: str | None = Field(default=None, max_length=255)
    partner_in_charge: str | None = Field(default=None, max_length=255)


class ClientRead(ClientBase):
    """Response shape for a single client, per API_SPEC.md."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ClientListResponse(BaseModel):
    """Response shape for GET /clients, per API_SPEC.md."""

    items: list[ClientRead]
    total: int
