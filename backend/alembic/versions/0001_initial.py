"""initial schema with pgvector

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("monthly_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plans_code", "plans", ["code"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    op.create_table(
        "document_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_name", sa.String(length=120), nullable=False),
        sa.Column("start_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.Text(), nullable=False),
    )
    op.create_index("ix_document_sections_document_id", "document_sections", ["document_id"])
    op.create_index("ix_document_sections_section_name", "document_sections", ["section_name"])

    op.create_table(
        "text_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("fingerprint_hashes", sa.JSON(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_position", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index("ix_text_chunks_document_id", "text_chunks", ["document_id"])
    op.create_index("ix_text_chunks_section_id", "text_chunks", ["section_id"])

    op.create_table(
        "chunk_fingerprints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hash_value", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_chunk_fingerprints_chunk_id", "chunk_fingerprints", ["chunk_id"])
    op.create_index("ix_chunk_fingerprints_hash_value", "chunk_fingerprints", ["hash_value"])

    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False, server_default="768"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chunk_embeddings_chunk_id", "chunk_embeddings", ["chunk_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunk_embeddings_embedding_cosine "
        "ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "similarity_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("global_similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("literal_similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("near_literal_similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("similarity_excluding_references_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("section_similarity", sa.JSON(), nullable=False),
        sa.Column("source_summary", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("exclude_references", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_similarity_reports_document_id", "similarity_reports", ["document_id"])
    op.create_index("ix_similarity_reports_owner_id", "similarity_reports", ["owner_id"])
    op.create_index("ix_similarity_reports_status", "similarity_reports", ["status"])

    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("similarity_reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])

    op.create_table(
        "similarity_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("similarity_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_chunk_id", sa.Integer(), sa.ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_chunk_id", sa.Integer(), sa.ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("jaccard_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fuzzy_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("semantic_similarity", sa.Float(), nullable=True),
        sa.Column("shared_fingerprint_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("match_type", sa.String(length=64), nullable=False),
        sa.Column("target_section", sa.String(length=120), nullable=False),
        sa.Column("source_section", sa.String(length=120), nullable=False),
        sa.Column("is_common_method_phrase", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("common_phrase_labels", sa.JSON(), nullable=False),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("target_start_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_end_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_start_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_end_position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_similarity_matches_report_id", "similarity_matches", ["report_id"])
    op.create_index("ix_similarity_matches_source_document_id", "similarity_matches", ["source_document_id"])
    op.create_index("ix_similarity_matches_match_type", "similarity_matches", ["match_type"])
    op.create_index("ix_similarity_matches_target_section", "similarity_matches", ["target_section"])
    op.create_index("ix_similarity_matches_is_common_method_phrase", "similarity_matches", ["is_common_method_phrase"])


def downgrade() -> None:
    op.drop_table("similarity_matches")
    op.drop_table("credit_transactions")
    op.drop_table("similarity_reports")
    op.drop_table("chunk_embeddings")
    op.drop_table("chunk_fingerprints")
    op.drop_table("text_chunks")
    op.drop_table("document_sections")
    op.drop_table("documents")
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("users")
