"""SQLAlchemy engine and session factories for Anne."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def build_anne_conninfo() -> str:
    dsn = os.getenv("ANNE_POSTGRES_DSN")
    if dsn:
        return dsn

    host = os.getenv("ANNE_POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("ANNE_POSTGRES_PORT", "5432")
    dbname = os.getenv("ANNE_POSTGRES_DB", "anne")
    user = os.getenv("ANNE_POSTGRES_USER", "anne")
    password = os.getenv("ANNE_POSTGRES_PASSWORD", "anne_dev_password")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def build_anne_sqlalchemy_url() -> str:
    dsn = os.getenv("ANNE_POSTGRES_DSN")
    if dsn:
        return dsn if "://" in dsn else f"postgresql+psycopg:///?{dsn.replace(' ', '&')}"

    host = os.getenv("ANNE_POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("ANNE_POSTGRES_PORT", "5432")
    dbname = os.getenv("ANNE_POSTGRES_DB", "anne")
    user = os.getenv("ANNE_POSTGRES_USER", "anne")
    password = os.getenv("ANNE_POSTGRES_PASSWORD", "anne_dev_password")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"


def create_anne_engine(url: str | None = None) -> Engine:
    try:
        return create_engine(url or build_anne_sqlalchemy_url(), future=True)
    except ImportError as exc:
        raise RuntimeError("sqlalchemy and psycopg are required to access Anne PostgreSQL") from exc


def create_anne_session(url: str | None = None, *, engine: Engine | None = None) -> Session:
    resolved_engine = engine or create_anne_engine(url)
    factory = sessionmaker(bind=resolved_engine, future=True)
    return factory()
