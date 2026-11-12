"""Registry facade over the canonical local resource/discovery tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import ResearchStore


class SQLiteResourceRegistry:
    """Ingest source catalogs as discovered-only records; never installs tools."""

    def __init__(self, store: ResearchStore):
        self.store = store

    def ingest(self, resources_path: str | Path, discoveries_path: str | Path) -> dict[str, int]:
        return self.store.import_registries(resources_path, discoveries_path)

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM resources"
        args: tuple[Any, ...] = ()
        if status:
            query += " WHERE status=?"
            args = (status,)
        query += " ORDER BY name"
        return [dict(row) for row in self.store.db.execute(query, args)]
