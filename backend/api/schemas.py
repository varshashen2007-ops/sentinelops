from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    severity: str | None = None


class TimelineEventResponse(BaseModel):
    timestamp: datetime
    source: str
    event_type: str
    resource: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class DiagnosisResponse(BaseModel):
    incident_id: str
    diagnosis: str | None = None
    confidence: float | None = None


class EvidenceResponse(BaseModel):
    evidence_id: str
    source: str
    evidence_type: str
    timestamp: datetime
    resource: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    recommendation_id: str
    action: str
    target: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str


class RemediationRequest(BaseModel):
    action_type: str
    resource_type: str
    namespace: str = Field(min_length=1, max_length=253)
    resource_name: str = Field(min_length=1, max_length=253)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("namespace", "resource_name")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("value must not be empty")

        return value


class RemediationResponse(BaseModel):
    action_type: str
    resource_type: str
    namespace: str
    resource_name: str
    dry_run: bool
    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)