"""SQLAlchemy persistence schema. Provider integrations stay outside this layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    project_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ResearchQuestion(Base):
    __tablename__ = "research_questions"
    question_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="draft")


class Source(Base):
    __tablename__ = "sources"
    source_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(40))
    license_status: Mapped[str] = mapped_column(String(40), default="unknown")


class PaperSnapshot(Base):
    __tablename__ = "paper_snapshots"
    snapshot_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.source_id"), index=True)
    content_sha256: Mapped[str] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    artifact_id: Mapped[str | None] = mapped_column(String(200))


class Claim(Base):
    __tablename__ = "claims"
    claim_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    verification_state: Mapped[str] = mapped_column(String(40), default="extracted")


class EvidenceEdge(Base):
    __tablename__ = "evidence_edges"
    edge_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.source_id"), index=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.claim_id"), index=True)
    location: Mapped[str] = mapped_column(Text)
    polarity: Mapped[str] = mapped_column(String(20))
    verification_state: Mapped[str] = mapped_column(String(40), default="unverified")


class Hypothesis(Base):
    __tablename__ = "hypotheses"
    hypothesis_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(30), default="exploratory")
    status: Mapped[str] = mapped_column(String(30), default="draft")


class ExperimentContract(Base):
    __tablename__ = "experiment_contracts"
    contract_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.hypothesis_id"), index=True)
    contract_sha256: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    approval_id: Mapped[str | None] = mapped_column(String(200))
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExperimentRun(Base):
    __tablename__ = "experiment_runs_api"
    run_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("experiment_contracts.contract_id"), index=True)
    seed: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    code_sha256: Mapped[str | None] = mapped_column(String(64))
    config_sha256: Mapped[str | None] = mapped_column(String(64))
    data_sha256: Mapped[str | None] = mapped_column(String(64))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    exception: Mapped[str | None] = mapped_column(Text)


class Artifact(Base):
    __tablename__ = "artifacts"
    artifact_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(40))
    owner_id: Mapped[str] = mapped_column(String(200), index=True)
    object_uri: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(120))


class Budget(Base):
    __tablename__ = "budgets"
    budget_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    limits: Mapped[dict[str, Any]] = mapped_column(JSON)
    spent: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Approval(Base):
    __tablename__ = "approvals"
    approval_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    workflow_id: Mapped[str | None] = mapped_column(String(200), index=True)
    action: Mapped[str] = mapped_column(String(100))
    scope: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(20))
    reviewed_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    workflow_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    run_key: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    state: Mapped[str] = mapped_column(String(30), default="queued")
    checkpoint: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    budget_id: Mapped[str | None] = mapped_column(ForeignKey("budgets.budget_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    error: Mapped[str | None] = mapped_column(Text)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    event_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.workflow_id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("workflow_id", "sequence", name="uq_workflow_event_sequence"),)


class Resource(Base):
    __tablename__ = "resource_registry"
    resource_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    canonical_url: Mapped[str] = mapped_column(Text, index=True)
    kind: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(Text)
    maintainer: Mapped[str | None] = mapped_column(Text)
    license_status: Mapped[str] = mapped_column(String(50), default="unknown")
    version_or_commit: Mapped[str | None] = mapped_column(String(200))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    integration_status: Mapped[str] = mapped_column(String(30), default="discovered")
    execution_risk: Mapped[str] = mapped_column(String(50), default="unreviewed")
    notes: Mapped[str] = mapped_column(Text, default="")
    source_payload: Mapped[dict[str, Any]] = mapped_column(JSON)

    @property
    def id(self) -> str:
        return self.resource_id


class ResourceObservation(Base):
    __tablename__ = "resource_observations"
    observation_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resource_registry.resource_id"), index=True)
    source_id: Mapped[str] = mapped_column(String(200), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class DiscoveryIndex(Base):
    __tablename__ = "discovery_indexes"
    index_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    index_type: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    authority: Mapped[str] = mapped_column(String(200))
    priority: Mapped[str] = mapped_column(String(20))
    verified_state: Mapped[str] = mapped_column(String(80))
    date_checked: Mapped[str | None] = mapped_column(String(40))
    source_payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class CapabilityEntry(Base):
    __tablename__ = "capability_registry"
    capability_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    version: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(String(200))
    integration_status: Mapped[str] = mapped_column(String(40), default="discovered")
    execution_risk: Mapped[str] = mapped_column(Text)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    secrets: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
