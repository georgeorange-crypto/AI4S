"""SQLAlchemy engine/session factory configurable for SQLite or PostgreSQL."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def database_url() -> str:
    return os.getenv("AI4S_DATABASE_URL", "sqlite:///./.ai4s/api.sqlite")


def make_engine(url: str | None = None) -> Engine:
    selected = url or database_url()
    if selected.startswith("sqlite:"):
        from sqlalchemy.engine import make_url

        database = make_url(selected).database
        if database and database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
    options = {"check_same_thread": False} if selected.startswith("sqlite") else {}
    return create_engine(selected, future=True, pool_pre_ping=True, connect_args=options)


engine = make_engine()
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
