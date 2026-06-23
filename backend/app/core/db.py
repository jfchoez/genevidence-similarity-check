from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import Plan  # noqa: F401
    from app.models import BaseModelImportMarker  # noqa: F401
    from app.services.billing import seed_default_plans

    if settings.DATABASE_URL.startswith("postgresql"):
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)
    _apply_runtime_schema_compatibility()

    with SessionLocal() as db:
        seed_default_plans(db)


def _apply_runtime_schema_compatibility() -> None:
    """Small additive migration guard for Vercel deployments using AUTO_CREATE_TABLES."""
    with engine.begin() as conn:
        dialect = conn.dialect.name
        if dialect == "postgresql":
            conn.execute(
                text(
                    "ALTER TABLE similarity_matches "
                    "ADD COLUMN IF NOT EXISTS source_kind VARCHAR(64) NOT NULL DEFAULT 'internal'"
                )
            )
            conn.execute(text("ALTER TABLE similarity_matches ALTER COLUMN source_document_id DROP NOT NULL"))
            conn.execute(text("ALTER TABLE similarity_matches ALTER COLUMN source_chunk_id DROP NOT NULL"))
            conn.execute(
                text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_id VARCHAR(255)")
            )
            conn.execute(
                text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_provider VARCHAR(120)")
            )
            conn.execute(
                text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_title VARCHAR(512)")
            )
            conn.execute(
                text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_url VARCHAR(1024)")
            )
            conn.execute(
                text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_doi VARCHAR(255)")
            )
            conn.execute(text("ALTER TABLE similarity_matches ADD COLUMN IF NOT EXISTS external_source_year INTEGER"))
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_similarity_matches_source_kind "
                    "ON similarity_matches (source_kind)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_similarity_matches_external_source_id "
                    "ON similarity_matches (external_source_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_similarity_matches_external_source_provider "
                    "ON similarity_matches (external_source_provider)"
                )
            )
        elif dialect == "sqlite":
            existing = {row[1] for row in conn.execute(text("PRAGMA table_info(similarity_matches)"))}
            columns = {
                "source_kind": "VARCHAR(64) NOT NULL DEFAULT 'internal'",
                "external_source_id": "VARCHAR(255)",
                "external_source_provider": "VARCHAR(120)",
                "external_source_title": "VARCHAR(512)",
                "external_source_url": "VARCHAR(1024)",
                "external_source_doi": "VARCHAR(255)",
                "external_source_year": "INTEGER",
            }
            for column, definition in columns.items():
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE similarity_matches ADD COLUMN {column} {definition}"))
