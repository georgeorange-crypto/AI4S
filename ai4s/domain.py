"""Validated API/domain contracts, independent of HTTP and persistence vendors."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(DomainModel):
    project_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=300)
    domain: str = "computer-science"


class ProjectRead(ProjectCreate):
    created_at: datetime


class QuestionCreate(DomainModel):
    question_id: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=10, max_length=4000)
    constraints: dict[str, Any] = Field(default_factory=dict)


class SourceCreate(DomainModel):
    source_id: str = Field(min_length=1, max_length=200)
    url: str
    title: str
    content_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    source_type: str = "fixture"


class ClaimCreate(DomainModel):
    claim_id: str
    content: str = Field(min_length=1)
    verification_state: Literal["extracted", "verified", "disputed", "unsupported"] = "extracted"


class EvidenceEdgeCreate(DomainModel):
    source_id: str
    claim_id: str
    location: str
    polarity: Literal["supports", "refutes", "context"]


class HypothesisCreate(DomainModel):
    hypothesis_id: str
    statement: str = Field(min_length=10)
    intent: Literal["exploratory", "confirmatory"] = "exploratory"


class ExperimentContractCreate(DomainModel):
    contract_id: str
    hypothesis_id: str
    contract_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    payload: dict[str, Any]
    approval_id: str | None = None


class ApprovalCreate(DomainModel):
    approval_id: str
    action: str
    scope: str
    decision: Literal["approved", "denied"]
    human_principal: str = Field(min_length=1)


class WorkflowCreate(DomainModel):
    workflow_id: str
    run_key: str
    project_id: str
    budget_id: str | None = None


class WorkflowControl(DomainModel):
    action: Literal["pause", "resume", "cancel"]
    reason: str = Field(min_length=1, max_length=1000)


class ResourceRead(DomainModel):
    id: str
    canonical_url: str
    kind: str
    name: str
    maintainer: str | None
    license_status: str
    version_or_commit: str | None
    discovered_at: datetime
    last_checked: datetime | None
    integration_status: str
    execution_risk: str
    notes: str


class CapabilityRead(DomainModel):
    capability_id: str
    version: str
    source: str
    license: str
    integration_status: str
    execution_risk: str
    permissions: list[str]
    secrets: list[str]
    evidence: list[str]


class WorkflowRead(DomainModel):
    workflow_id: str
    run_key: str
    project_id: str
    state: str
    created_at: datetime


class EventRead(DomainModel):
    event_id: str
    workflow_id: str
    sequence: int
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
