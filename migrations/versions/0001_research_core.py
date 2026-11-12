"""Initial typed research domain and workflow schema.

Revision ID: 0001_research_core
Revises:
"""

from alembic import op

from ai4s.orm import Base

revision = "0001_research_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    names = (
        "projects",
        "research_questions",
        "sources",
        "paper_snapshots",
        "claims",
        "evidence_edges",
        "hypotheses",
        "experiment_contracts",
        "experiment_runs_api",
        "artifacts",
        "budgets",
        "approvals",
        "workflow_runs",
        "workflow_events",
        "resource_registry",
        "resource_observations",
        "discovery_indexes",
    )
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in names])


def downgrade() -> None:
    names = (
        "discovery_indexes",
        "resource_observations",
        "resource_registry",
        "workflow_events",
        "workflow_runs",
        "approvals",
        "budgets",
        "artifacts",
        "experiment_runs_api",
        "experiment_contracts",
        "hypotheses",
        "evidence_edges",
        "claims",
        "paper_snapshots",
        "sources",
        "research_questions",
        "projects",
    )
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in names])
