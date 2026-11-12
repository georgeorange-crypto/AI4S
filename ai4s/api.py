"""Loopback-oriented HTTP control plane for research records and workflows."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_session
from .domain import (
    CapabilityRead,
    EventRead,
    ProjectCreate,
    ProjectRead,
    QuestionCreate,
    ResourceRead,
    WorkflowControl,
    WorkflowCreate,
    WorkflowRead,
)
from .orm import CapabilityEntry, Project, ResearchQuestion, Resource, WorkflowEvent, WorkflowRun

app = FastAPI(title="AI4S Research OS API", version="0.1.0")


@app.get("/healthz")
def healthz(session: Session = Depends(get_session)) -> dict[str, str]:
    session.execute(select(1))
    return {"status": "ok"}


@app.post("/api/v1/projects", response_model=ProjectRead, status_code=201)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    if session.get(Project, body.project_id):
        raise HTTPException(409, "project_id already exists")
    row = Project(**body.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@app.get("/api/v1/projects", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_session)) -> list[Project]:
    return list(session.scalars(select(Project).order_by(Project.created_at.desc())))


@app.post("/api/v1/projects/{project_id}/questions", status_code=201)
def create_question(project_id: str, body: QuestionCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    if not session.get(Project, project_id):
        raise HTTPException(404, "project not found")
    if session.get(ResearchQuestion, body.question_id):
        raise HTTPException(409, "question_id already exists")
    row = ResearchQuestion(project_id=project_id, **body.model_dump())
    session.add(row)
    session.commit()
    return {"question_id": row.question_id, "project_id": project_id, "question": row.question, "status": row.status}


@app.get("/api/v1/resources", response_model=list[ResourceRead])
def list_resources(
    status: str | None = None, limit: int = 100, session: Session = Depends(get_session)
) -> list[Resource]:
    if limit < 1 or limit > 500:
        raise HTTPException(422, "limit must be between 1 and 500")
    stmt = select(Resource)
    if status:
        stmt = stmt.where(Resource.integration_status == status)
    return list(session.scalars(stmt.order_by(Resource.name).limit(limit)))


@app.get("/api/v1/capabilities", response_model=list[CapabilityRead])
def list_capabilities(session: Session = Depends(get_session)) -> list[CapabilityEntry]:
    """List only explicitly audited runtime capabilities; discovered candidates stay separate."""
    return list(session.scalars(select(CapabilityEntry).order_by(CapabilityEntry.capability_id)))


@app.post("/api/v1/workflows", response_model=WorkflowRead, status_code=201)
def create_workflow(body: WorkflowCreate, session: Session = Depends(get_session)) -> WorkflowRun:
    if not session.get(Project, body.project_id):
        raise HTTPException(404, "project not found")
    existing = session.scalar(select(WorkflowRun).where(WorkflowRun.run_key == body.run_key))
    if existing:
        return existing
    row = WorkflowRun(**body.model_dump())
    session.add(row)
    session.flush()
    session.add(
        WorkflowEvent(
            event_id=str(uuid.uuid4()),
            workflow_id=row.workflow_id,
            sequence=1,
            event_type="workflow_created",
            payload={"run_key": row.run_key},
        )
    )
    session.commit()
    session.refresh(row)
    return row


@app.post("/api/v1/workflows/{workflow_id}/control", response_model=WorkflowRead)
def control_workflow(workflow_id: str, body: WorkflowControl, session: Session = Depends(get_session)) -> WorkflowRun:
    row = session.get(WorkflowRun, workflow_id)
    if not row:
        raise HTTPException(404, "workflow not found")
    allowed = {
        "queued": {"cancel", "pause"},
        "running": {"pause", "cancel"},
        "paused": {"resume", "cancel"},
        "failed": {"resume", "cancel"},
    }
    if body.action not in allowed.get(row.state, set()):
        raise HTTPException(409, f"invalid workflow action {body.action!r} for state {row.state!r}")
    previous = row.state
    row.state = {"pause": "paused", "resume": "running", "cancel": "cancelled"}[body.action]
    last_sequence = session.scalar(
        select(func.coalesce(func.max(WorkflowEvent.sequence), 0)).where(WorkflowEvent.workflow_id == workflow_id)
    )
    seq = (last_sequence or 0) + 1
    session.add(
        WorkflowEvent(
            event_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            sequence=seq,
            event_type="state_changed",
            payload={"from": previous, "to": row.state, "reason": body.reason},
        )
    )
    session.commit()
    session.refresh(row)
    return row


@app.get("/api/v1/workflows/{workflow_id}/events", response_model=list[EventRead])
def list_events(workflow_id: str, session: Session = Depends(get_session)) -> list[WorkflowEvent]:
    if not session.get(WorkflowRun, workflow_id):
        raise HTTPException(404, "workflow not found")
    return list(
        session.scalars(
            select(WorkflowEvent).where(WorkflowEvent.workflow_id == workflow_id).order_by(WorkflowEvent.sequence)
        )
    )
