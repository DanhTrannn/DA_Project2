from __future__ import annotations

import os

from sqlalchemy import create_engine, text


def database_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("SOURCE_HOST", "db")
    port = os.getenv("SOURCE_INTERNAL_PORT", "5432")
    database = os.getenv("SOURCE_DATABASE", "Adventureworks")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def engine():
    return create_engine(database_url())


def ensure_analytics_schema() -> None:
    with engine().begin() as connection:
        connection.execute(text("create schema if not exists analytics"))
