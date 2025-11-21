"""
Post-install / post-document helpers for database configuration

Provides convenient initialization and factory helpers for the parser to
obtain connection strings, SQLAlchemy engines and session makers using the
`DatabaseConfig` and `PostgreSQLConfig` defined in `db_config.py`.

This module intentionally keeps a lightweight surface so parser code can call
`init_db()` early and then use one-line helpers such as `get_sync_engine()` or
`get_connection_string()` when building DB-backed parsing/export flows.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from .db_config import DatabaseConfig, db_config

# Public module-level configuration instance. Call `init_db()` to reload from
# environment if needed; by default it uses the already-loaded `db_config`.
config: DatabaseConfig = db_config


def init_db() -> DatabaseConfig:
    """Re-load database configuration and return it.
    Returns:
        The initialized `DatabaseConfig` instance.
    """
    global config
    # DatabaseConfig.load uses PostgreSQLConfig.from_env internally which
    # reads environment variables (python-dotenv is loaded in db_config).
    config = DatabaseConfig.load()
    return config


def get_connection_string(async_driver: bool = False) -> str:
    """Get the SQLAlchemy connection string for the configured PostgreSQL.

    Args:
        async_driver: If True, returns an async driver connection string.
    """
    return config.postgresql.get_connection_string(async_driver=async_driver)


def get_engine_kwargs() -> dict:
    """Return engine kwargs suitable for SQLAlchemy `create_engine` call."""
    return config.postgresql.get_engine_kwargs()


def get_sync_engine() -> Engine:
    """Create and return a synchronous SQLAlchemy Engine using the config."""
    conn = get_connection_string(async_driver=False)
    kwargs = get_engine_kwargs()
    return create_engine(conn, **kwargs)


def get_async_engine() -> AsyncEngine:
    """Create and return an asynchronous SQLAlchemy AsyncEngine using config."""
    conn = get_connection_string(async_driver=True)
    kwargs = get_engine_kwargs()
    # SQLAlchemy async engines accept the same general kwargs for pool
    return create_async_engine(conn, **kwargs)


def make_sync_session_factory(**session_kwargs) -> sessionmaker:
    """Return a sync `sessionmaker` bound to the sync engine."""
    engine = get_sync_engine()
    return sessionmaker(bind=engine, expire_on_commit=False, **session_kwargs)


def make_async_session_factory(**session_kwargs) -> sessionmaker:
    """Return an async `sessionmaker` producing `AsyncSession` instances."""
    engine = get_async_engine()
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, **session_kwargs)


__all__ = [
    "config",
    "init_db",
    "get_connection_string",
    "get_engine_kwargs",
    "get_sync_engine",
    "get_async_engine",
    "make_sync_session_factory",
    "make_async_session_factory",
]
