from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ChunkFingerprint, Document, DocumentSection, MatchType, TextChunk
from app.services.text_processing import find_common_method_phrases


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


@dataclass(frozen=True)
class ScoredCandidate:
    chunk: TextChunk
    shared_fingerprint_count: int
    jaccard_score: float
    fuzzy_score: float
    similarity_score: float
    match_type: str | None
    common_phrase_labels: list[str]

    @property
    def is_relevant(self) -> bool:
        return self.match_type is not None


class SimilarityEngine:
    def __init__(
        self,
        jaccard_threshold: float | None = None,
        fuzzy_threshold: int | None = None,
    ) -> None:
        self.jaccard_threshold = jaccard_threshold or settings.JACCARD_THRESHOLD
        self.fuzzy_threshold = fuzzy_threshold or settings.FUZZY_THRESHOLD

    def retrieve_literal_candidates(
        self,
        db: Session,
        target_chunk: TextChunk,
        target_document_id: int,
        exclude_references: bool = False,
        limit: int = 50,
    ) -> list[tuple[TextChunk, int]]:
        hashes = list(set(target_chunk.fingerprint_hashes or []))
        if not hashes:
            return []

        query = (
            db.query(TextChunk, func.count(ChunkFingerprint.id).label("shared_count"))
            .join(ChunkFingerprint, ChunkFingerprint.chunk_id == TextChunk.id)
            .join(Document, Document.id == TextChunk.document_id)
            .outerjoin(DocumentSection, DocumentSection.id == TextChunk.section_id)
            .filter(ChunkFingerprint.hash_value.in_(hashes))
            .filter(TextChunk.document_id != target_document_id)
            .filter(Document.status == "indexed")
        )

        if exclude_references:
            query = query.filter(
                (DocumentSection.id.is_(None)) | (DocumentSection.section_name != "referencias")
            )

        query = query.group_by(TextChunk.id).order_by(desc("shared_count")).limit(limit)

        return [(chunk, int(shared_count)) for chunk, shared_count in query.all()]

    def score_pair(
        self,
        target_chunk: TextChunk,
        source_chunk: TextChunk,
        shared_fingerprint_count: int = 0,
    ) -> ScoredCandidate:
        target_hashes = set(target_chunk.fingerprint_hashes or [])
        source_hashes = set(source_chunk.fingerprint_hashes or [])
        jaccard_score = jaccard_similarity(target_hashes, source_hashes)
        fuzzy_score = float(fuzz.token_set_ratio(target_chunk.normalized_text, source_chunk.normalized_text))
        similarity_score = max(jaccard_score * 100.0, fuzzy_score)
        match_type = self.classify(jaccard_score, fuzzy_score, target_chunk, source_chunk)
        phrases = find_common_method_phrases(target_chunk.text) + find_common_method_phrases(source_chunk.text)
        return ScoredCandidate(
            chunk=source_chunk,
            shared_fingerprint_count=shared_fingerprint_count,
            jaccard_score=round(jaccard_score * 100.0, 2),
            fuzzy_score=round(fuzzy_score, 2),
            similarity_score=round(min(100.0, similarity_score), 2),
            match_type=match_type,
            common_phrase_labels=sorted(set(phrases)),
        )

    def classify(
        self,
        jaccard_score: float,
        fuzzy_score: float,
        target_chunk: TextChunk,
        source_chunk: TextChunk,
    ) -> str | None:
        if target_chunk.normalized_text == source_chunk.normalized_text:
            return MatchType.exact.value
        if jaccard_score >= 0.65 and fuzzy_score >= 95:
            return MatchType.exact.value
        if fuzzy_score >= self.fuzzy_threshold:
            return MatchType.near_exact.value
        if jaccard_score >= self.jaccard_threshold:
            return MatchType.partial.value
        return None
