from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.core.db import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - optional outside PostgreSQL installs
    Vector = None


class PgVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())


class UserRole(str, Enum):
    admin = "admin"
    reviewer = "reviewer"
    user = "user"


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class ReportStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class MatchType(str, Enum):
    exact = "exact"
    near_exact = "near_exact"
    partial = "partial"
    possible_paraphrase = "possible_paraphrase"


class SourceKind(str, Enum):
    internal = "internal"
    external_academic = "external_academic"


class SubscriptionStatus(str, Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(32), default=UserRole.user.value, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    documents = relationship("Document", back_populates="owner")
    reports = relationship("SimilarityReport", back_populates="owner")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    monthly_credits = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String(32), default=SubscriptionStatus.active.value, nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    plan = relationship("Plan", back_populates="subscriptions")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    report_id = Column(Integer, ForeignKey("similarity_reports.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(16), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    extracted_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    status = Column(String(32), default=DocumentStatus.uploaded.value, nullable=False, index=True)
    word_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner = relationship("User", back_populates="documents")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("SimilarityReport", back_populates="document")


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    section_name = Column(String(120), default="seccion no detectada", nullable=False, index=True)
    start_position = Column(Integer, default=0, nullable=False)
    end_position = Column(Integer, default=0, nullable=False)
    text = Column(Text, nullable=False)

    document = relationship("Document", back_populates="sections")
    chunks = relationship("TextChunk", back_populates="section")


class TextChunk(Base):
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    fingerprint_hashes = Column(JSON, default=list, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    start_position = Column(Integer, default=0, nullable=False)
    end_position = Column(Integer, default=0, nullable=False)

    document = relationship("Document", back_populates="chunks")
    section = relationship("DocumentSection", back_populates="chunks")
    fingerprints = relationship("ChunkFingerprint", back_populates="chunk", cascade="all, delete-orphan")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),)


class ChunkFingerprint(Base):
    __tablename__ = "chunk_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    hash_value = Column(String(32), nullable=False, index=True)
    position = Column(Integer, default=0, nullable=False)

    chunk = relationship("TextChunk", back_populates="fingerprints")


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("text_chunks.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    model_name = Column(String(255), nullable=False)
    dimensions = Column(Integer, default=settings.SEMANTIC_EMBEDDING_DIMENSIONS, nullable=False)
    embedding = Column(PgVector(settings.SEMANTIC_EMBEDDING_DIMENSIONS), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chunk = relationship("TextChunk", back_populates="embedding")


class SimilarityReport(Base):
    __tablename__ = "similarity_reports"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), default=ReportStatus.pending.value, nullable=False, index=True)
    global_similarity_score = Column(Float, default=0.0, nullable=False)
    literal_similarity_score = Column(Float, default=0.0, nullable=False)
    near_literal_similarity_score = Column(Float, default=0.0, nullable=False)
    similarity_excluding_references_score = Column(Float, default=0.0, nullable=False)
    section_similarity = Column(JSON, default=dict, nullable=False)
    source_summary = Column(JSON, default=list, nullable=False)
    warnings = Column(JSON, default=list, nullable=False)
    exclude_references = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    document = relationship("Document", back_populates="reports")
    owner = relationship("User", back_populates="reports")
    matches = relationship("SimilarityMatch", back_populates="report", cascade="all, delete-orphan")


class SimilarityMatch(Base):
    __tablename__ = "similarity_matches"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("similarity_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    source_kind = Column(String(64), default=SourceKind.internal.value, nullable=False, index=True)
    source_document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    target_chunk_id = Column(Integer, ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    source_chunk_id = Column(Integer, ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=True, index=True)
    external_source_id = Column(String(255), nullable=True, index=True)
    external_source_provider = Column(String(120), nullable=True, index=True)
    external_source_title = Column(String(512), nullable=True)
    external_source_url = Column(String(1024), nullable=True)
    external_source_doi = Column(String(255), nullable=True)
    external_source_year = Column(Integer, nullable=True)
    similarity_score = Column(Float, nullable=False)
    jaccard_score = Column(Float, default=0.0, nullable=False)
    fuzzy_score = Column(Float, default=0.0, nullable=False)
    semantic_similarity = Column(Float, nullable=True)
    shared_fingerprint_count = Column(Integer, default=0, nullable=False)
    match_type = Column(String(64), nullable=False, index=True)
    target_section = Column(String(120), default="seccion no detectada", nullable=False, index=True)
    source_section = Column(String(120), default="seccion no detectada", nullable=False, index=True)
    is_common_method_phrase = Column(Boolean, default=False, nullable=False, index=True)
    common_phrase_labels = Column(JSON, default=list, nullable=False)
    target_text = Column(Text, nullable=False)
    source_text = Column(Text, nullable=False)
    target_start_position = Column(Integer, default=0, nullable=False)
    target_end_position = Column(Integer, default=0, nullable=False)
    source_start_position = Column(Integer, default=0, nullable=False)
    source_end_position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("SimilarityReport", back_populates="matches")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    target_chunk = relationship("TextChunk", foreign_keys=[target_chunk_id])
    source_chunk = relationship("TextChunk", foreign_keys=[source_chunk_id])


class BaseModelImportMarker:
    pass
