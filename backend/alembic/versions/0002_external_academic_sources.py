"""support external academic sources in similarity matches

Revision ID: 0002_external_academic_sources
Revises: 0001_initial
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_external_academic_sources"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "similarity_matches",
        sa.Column("source_kind", sa.String(length=64), nullable=False, server_default="internal"),
    )
    op.alter_column("similarity_matches", "source_document_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("similarity_matches", "source_chunk_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("similarity_matches", sa.Column("external_source_id", sa.String(length=255), nullable=True))
    op.add_column("similarity_matches", sa.Column("external_source_provider", sa.String(length=120), nullable=True))
    op.add_column("similarity_matches", sa.Column("external_source_title", sa.String(length=512), nullable=True))
    op.add_column("similarity_matches", sa.Column("external_source_url", sa.String(length=1024), nullable=True))
    op.add_column("similarity_matches", sa.Column("external_source_doi", sa.String(length=255), nullable=True))
    op.add_column("similarity_matches", sa.Column("external_source_year", sa.Integer(), nullable=True))
    op.create_index("ix_similarity_matches_source_kind", "similarity_matches", ["source_kind"])
    op.create_index("ix_similarity_matches_external_source_id", "similarity_matches", ["external_source_id"])
    op.create_index(
        "ix_similarity_matches_external_source_provider",
        "similarity_matches",
        ["external_source_provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_similarity_matches_external_source_provider", table_name="similarity_matches")
    op.drop_index("ix_similarity_matches_external_source_id", table_name="similarity_matches")
    op.drop_index("ix_similarity_matches_source_kind", table_name="similarity_matches")
    op.drop_column("similarity_matches", "external_source_year")
    op.drop_column("similarity_matches", "external_source_doi")
    op.drop_column("similarity_matches", "external_source_url")
    op.drop_column("similarity_matches", "external_source_title")
    op.drop_column("similarity_matches", "external_source_provider")
    op.drop_column("similarity_matches", "external_source_id")
    op.alter_column("similarity_matches", "source_chunk_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("similarity_matches", "source_document_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("similarity_matches", "source_kind")
