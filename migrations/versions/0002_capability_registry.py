"""Add the audited runtime capability registry.

Revision ID: 0002_capability_registry
Revises: 0001_research_core
"""

from alembic import op

from ai4s.orm import Base

revision = "0002_capability_registry"
down_revision = "0001_research_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables["capability_registry"]])


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables["capability_registry"]])
