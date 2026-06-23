from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_filename: str
    file_type: str
    status: str
    word_count: int
    created_at: datetime
    error_message: str | None = None


class DocumentDetail(DocumentOut):
    sections: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []


class ReportMatchOut(BaseModel):
    id: int
    source_kind: str = "internal"
    source_document_id: int | None = None
    source_document_label: str
    target_chunk_id: int
    source_chunk_id: int | None = None
    external_source_id: str | None = None
    external_source_provider: str | None = None
    external_source_title: str | None = None
    external_source_url: str | None = None
    external_source_doi: str | None = None
    external_source_year: int | None = None
    similarity_score: float
    jaccard_score: float
    fuzzy_score: float
    semantic_similarity: float | None = None
    shared_fingerprint_count: int
    match_type: str
    target_section: str
    source_section: str
    is_common_method_phrase: bool
    common_phrase_labels: list[str]
    target_text: str
    source_text: str
    target_start_position: int
    target_end_position: int
    source_start_position: int
    source_end_position: int


class SourceSummaryOut(BaseModel):
    source_kind: str = "internal"
    source_document_id: int | None = None
    source_document_label: str
    external_source_id: str | None = None
    external_source_provider: str | None = None
    external_source_url: str | None = None
    match_count: int
    max_score: float
    matched_sections: list[str]


class ReportOut(BaseModel):
    id: int
    document_id: int
    document_title: str
    status: str
    global_similarity_score: float
    literal_similarity_score: float
    near_literal_similarity_score: float
    similarity_excluding_references_score: float
    section_similarity: dict[str, float]
    source_summary: list[SourceSummaryOut]
    warnings: list[str]
    exclude_references: bool
    created_at: datetime
    completed_at: datetime | None = None
    matches: list[ReportMatchOut]


class BillingCreditsOut(BaseModel):
    user_id: int
    available_credits: int
    plan: str


class AdminCreditGrant(BaseModel):
    amount: int
    reason: str = "admin_credit_adjustment"


class AdminStatsOut(BaseModel):
    total_users: int
    total_documents: int
    total_reports: int
    total_credit_consumed: int
