from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, status
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.core.common_phrases import ACADEMIC_REVIEW_WARNING, SEMANTIC_WARNING
from app.core.config import settings
from app.models import (
    Document,
    DocumentStatus,
    MatchType,
    ReportStatus,
    SimilarityMatch,
    SimilarityReport,
    TextChunk,
    User,
)
from app.schemas import ReportMatchOut, ReportOut, SourceSummaryOut
from app.services.billing import deduct_report_credit, get_credit_balance
from app.services.embeddings import SemanticSimilarityService, should_mark_possible_paraphrase
from app.services.similarity import SimilarityEngine
from app.services.text_processing import find_common_method_phrases


def can_view_document(user: User, document: Document) -> bool:
    return user.role == "admin" or document.owner_id == user.id


def assert_document_access(user: User, document: Document | None) -> Document:
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not can_view_document(user, document):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def can_view_report(user: User, report: SimilarityReport) -> bool:
    return user.role == "admin" or report.owner_id == user.id


def source_label_for_user(user: User, source_document: Document) -> str:
    if user.role == "admin" or source_document.owner_id == user.id:
        return source_document.title
    return f"Documento interno #{source_document.id}"


def privacy_trim_source_text(user: User, source_document: Document, text_value: str) -> str:
    if user.role == "admin" or source_document.owner_id == user.id:
        return text_value
    text_value = " ".join(text_value.split())
    return text_value[:360] + ("..." if len(text_value) > 360 else "")


class ReportGenerator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = SimilarityEngine()
        self.semantic = SemanticSimilarityService()

    def generate(
        self,
        document_id: int,
        user: User,
        exclude_references: bool = False,
    ) -> SimilarityReport:
        document = assert_document_access(user, self.db.get(Document, document_id))
        if document.status != DocumentStatus.indexed.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document must be indexed before generating a report",
            )
        if get_credit_balance(self.db, user.id) <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="No tienes creditos disponibles para generar reportes.",
            )

        report = SimilarityReport(
            document_id=document.id,
            owner_id=user.id,
            status=ReportStatus.processing.value,
            exclude_references=exclude_references,
            warnings=[ACADEMIC_REVIEW_WARNING, SEMANTIC_WARNING],
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        try:
            matches = self._build_matches(report, document, exclude_references)
            for match in matches:
                self.db.add(match)

            matched_ids_by_type: dict[str, set[int]] = defaultdict(set)
            all_matched_ids: set[int] = set()
            for match in matches:
                all_matched_ids.add(match.target_chunk_id)
                matched_ids_by_type[match.match_type].add(match.target_chunk_id)

            all_chunks = list(
                self.db.query(TextChunk)
                .filter(TextChunk.document_id == document.id)
                .order_by(TextChunk.chunk_index)
                .all()
            )
            report.global_similarity_score = self._score_chunks(
                all_chunks,
                all_matched_ids,
                exclude_references=exclude_references,
            )
            report.similarity_excluding_references_score = self._score_chunks(
                all_chunks,
                all_matched_ids,
                exclude_references=True,
            )
            report.literal_similarity_score = self._score_chunks(
                all_chunks,
                matched_ids_by_type.get(MatchType.exact.value, set()),
                exclude_references=exclude_references,
            )
            near_ids = (
                matched_ids_by_type.get(MatchType.near_exact.value, set())
                | matched_ids_by_type.get(MatchType.partial.value, set())
            )
            report.near_literal_similarity_score = self._score_chunks(
                all_chunks,
                near_ids,
                exclude_references=exclude_references,
            )
            report.section_similarity = self._section_similarity(all_chunks, all_matched_ids)
            report.source_summary = self._source_summary(matches)
            report.status = ReportStatus.completed.value
            report.completed_at = datetime.now(timezone.utc)

            deduct_report_credit(self.db, user.id, report.id)

            self.db.commit()
            self.db.refresh(report)
            return report
        except Exception as exc:
            self.db.rollback()
            report = self.db.get(SimilarityReport, report.id)
            if report:
                report.status = ReportStatus.failed.value
                report.error_message = str(exc)
                self.db.commit()
            raise

    def _build_matches(
        self,
        report: SimilarityReport,
        document: Document,
        exclude_references: bool,
    ) -> list[SimilarityMatch]:
        target_chunks = (
            self.db.query(TextChunk)
            .filter(TextChunk.document_id == document.id)
            .order_by(TextChunk.chunk_index)
            .all()
        )
        if exclude_references:
            target_chunks = [chunk for chunk in target_chunks if self._section_name(chunk) != "referencias"]

        matches: list[SimilarityMatch] = []
        seen_pairs: set[tuple[int, int]] = set()

        for target_chunk in target_chunks:
            candidates = self.engine.retrieve_literal_candidates(
                self.db,
                target_chunk,
                document.id,
                exclude_references=exclude_references,
            )
            scored = []
            for source_chunk, shared_count in candidates:
                pair = (target_chunk.id, source_chunk.id)
                if pair in seen_pairs:
                    continue
                score = self.engine.score_pair(target_chunk, source_chunk, shared_count)
                if score.is_relevant:
                    scored.append((source_chunk, score))

            for source_chunk, score in sorted(scored, key=lambda item: item[1].similarity_score, reverse=True)[:5]:
                seen_pairs.add((target_chunk.id, source_chunk.id))
                matches.append(
                    self._literal_match_from_score(
                        report.id,
                        target_chunk,
                        source_chunk,
                        score.match_type or MatchType.partial.value,
                        score.similarity_score,
                        score.jaccard_score,
                        score.fuzzy_score,
                        score.shared_fingerprint_count,
                        score.common_phrase_labels,
                    )
                )

        if settings.SEMANTIC_ENABLED:
            matches.extend(self._semantic_matches(report.id, document.id, target_chunks, seen_pairs))

        return matches

    def _semantic_matches(
        self,
        report_id: int,
        document_id: int,
        target_chunks: list[TextChunk],
        seen_pairs: set[tuple[int, int]],
    ) -> list[SimilarityMatch]:
        matches: list[SimilarityMatch] = []
        for target_chunk in target_chunks:
            if target_chunk.word_count < settings.SEMANTIC_MIN_WORDS:
                continue
            candidates = self.semantic.semantic_candidates(self.db, target_chunk, document_id, seen_pairs)
            for source_chunk_id, cosine_score in candidates:
                source_chunk = self.db.get(TextChunk, source_chunk_id)
                if not source_chunk:
                    continue
                fuzzy_score = float(
                    fuzz.token_set_ratio(target_chunk.normalized_text, source_chunk.normalized_text)
                )
                if not should_mark_possible_paraphrase(cosine_score, fuzzy_score, target_chunk.word_count):
                    continue
                seen_pairs.add((target_chunk.id, source_chunk.id))
                common_phrases = sorted(
                    set(find_common_method_phrases(target_chunk.text) + find_common_method_phrases(source_chunk.text))
                )
                matches.append(
                    SimilarityMatch(
                        report_id=report_id,
                        source_document_id=source_chunk.document_id,
                        target_chunk_id=target_chunk.id,
                        source_chunk_id=source_chunk.id,
                        similarity_score=round(cosine_score * 100.0, 2),
                        jaccard_score=0.0,
                        fuzzy_score=round(fuzzy_score, 2),
                        semantic_similarity=round(cosine_score, 4),
                        shared_fingerprint_count=0,
                        match_type=MatchType.possible_paraphrase.value,
                        target_section=self._section_name(target_chunk),
                        source_section=self._section_name(source_chunk),
                        is_common_method_phrase=bool(common_phrases),
                        common_phrase_labels=common_phrases,
                        target_text=target_chunk.text,
                        source_text=source_chunk.text,
                        target_start_position=target_chunk.start_position,
                        target_end_position=target_chunk.end_position,
                        source_start_position=source_chunk.start_position,
                        source_end_position=source_chunk.end_position,
                    )
                )
                break
        return matches

    def _literal_match_from_score(
        self,
        report_id: int,
        target_chunk: TextChunk,
        source_chunk: TextChunk,
        match_type: str,
        similarity_score: float,
        jaccard_score: float,
        fuzzy_score: float,
        shared_fingerprint_count: int,
        common_phrase_labels: list[str],
    ) -> SimilarityMatch:
        return SimilarityMatch(
            report_id=report_id,
            source_document_id=source_chunk.document_id,
            target_chunk_id=target_chunk.id,
            source_chunk_id=source_chunk.id,
            similarity_score=similarity_score,
            jaccard_score=jaccard_score,
            fuzzy_score=fuzzy_score,
            shared_fingerprint_count=shared_fingerprint_count,
            match_type=match_type,
            target_section=self._section_name(target_chunk),
            source_section=self._section_name(source_chunk),
            is_common_method_phrase=bool(common_phrase_labels),
            common_phrase_labels=common_phrase_labels,
            target_text=target_chunk.text,
            source_text=source_chunk.text,
            target_start_position=target_chunk.start_position,
            target_end_position=target_chunk.end_position,
            source_start_position=source_chunk.start_position,
            source_end_position=source_chunk.end_position,
        )

    @staticmethod
    def _section_name(chunk: TextChunk) -> str:
        if chunk.section and chunk.section.section_name:
            return chunk.section.section_name
        return "seccion no detectada"

    def _score_chunks(
        self,
        chunks: list[TextChunk],
        matched_ids: set[int],
        exclude_references: bool,
    ) -> float:
        eligible = [
            chunk
            for chunk in chunks
            if not exclude_references or self._section_name(chunk) != "referencias"
        ]
        total_words = sum(chunk.word_count for chunk in eligible)
        if total_words == 0:
            return 0.0
        matched_words = sum(chunk.word_count for chunk in eligible if chunk.id in matched_ids)
        return round(min(100.0, matched_words / total_words * 100.0), 2)

    def _section_similarity(self, chunks: list[TextChunk], matched_ids: set[int]) -> dict[str, float]:
        totals: dict[str, int] = defaultdict(int)
        matched: dict[str, int] = defaultdict(int)
        for chunk in chunks:
            section = self._section_name(chunk)
            totals[section] += chunk.word_count
            if chunk.id in matched_ids:
                matched[section] += chunk.word_count
        return {
            section: round(min(100.0, matched[section] / total * 100.0), 2)
            for section, total in totals.items()
            if total > 0
        }

    @staticmethod
    def _source_summary(matches: list[SimilarityMatch]) -> list[dict]:
        summary: dict[int, dict] = {}
        for match in matches:
            row = summary.setdefault(
                match.source_document_id,
                {
                    "source_document_id": match.source_document_id,
                    "match_count": 0,
                    "max_score": 0.0,
                    "matched_sections": set(),
                },
            )
            row["match_count"] += 1
            row["max_score"] = max(row["max_score"], match.similarity_score)
            row["matched_sections"].add(match.target_section)

        return [
            {
                "source_document_id": source_id,
                "match_count": data["match_count"],
                "max_score": round(data["max_score"], 2),
                "matched_sections": sorted(data["matched_sections"]),
            }
            for source_id, data in sorted(summary.items(), key=lambda item: item[1]["max_score"], reverse=True)
        ]


def build_report_response(
    db: Session,
    report: SimilarityReport,
    user: User,
    source: str | None = None,
    section: str | None = None,
    match_type: str | None = None,
    min_score: float | None = None,
) -> ReportOut:
    if not can_view_report(user, report):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    matches_query = db.query(SimilarityMatch).filter(SimilarityMatch.report_id == report.id)
    if section:
        matches_query = matches_query.filter(SimilarityMatch.target_section == section)
    if match_type:
        if match_type == "frase metodologica comun":
            matches_query = matches_query.filter(SimilarityMatch.is_common_method_phrase.is_(True))
        else:
            matches_query = matches_query.filter(SimilarityMatch.match_type == match_type)
    if min_score is not None:
        matches_query = matches_query.filter(SimilarityMatch.similarity_score >= min_score)
    if source:
        if source.isdigit():
            matches_query = matches_query.filter(SimilarityMatch.source_document_id == int(source))

    matches = matches_query.order_by(SimilarityMatch.similarity_score.desc()).all()
    if source and not source.isdigit():
        source_lower = source.lower()
        matches = [
            match
            for match in matches
            if source_lower in source_label_for_user(user, match.source_document).lower()
        ]

    source_summary = []
    for item in report.source_summary or []:
        source_document = db.get(Document, item["source_document_id"])
        if not source_document:
            continue
        source_summary.append(
            SourceSummaryOut(
                source_document_id=source_document.id,
                source_document_label=source_label_for_user(user, source_document),
                match_count=item.get("match_count", 0),
                max_score=item.get("max_score", 0.0),
                matched_sections=item.get("matched_sections", []),
            )
        )

    match_payloads: list[ReportMatchOut] = []
    for match in matches:
        match_payloads.append(
            ReportMatchOut(
                id=match.id,
                source_document_id=match.source_document_id,
                source_document_label=source_label_for_user(user, match.source_document),
                target_chunk_id=match.target_chunk_id,
                source_chunk_id=match.source_chunk_id,
                similarity_score=match.similarity_score,
                jaccard_score=match.jaccard_score,
                fuzzy_score=match.fuzzy_score,
                semantic_similarity=match.semantic_similarity,
                shared_fingerprint_count=match.shared_fingerprint_count,
                match_type=match.match_type,
                target_section=match.target_section,
                source_section=match.source_section,
                is_common_method_phrase=match.is_common_method_phrase,
                common_phrase_labels=match.common_phrase_labels or [],
                target_text=match.target_text,
                source_text=privacy_trim_source_text(user, match.source_document, match.source_text),
                target_start_position=match.target_start_position,
                target_end_position=match.target_end_position,
                source_start_position=match.source_start_position,
                source_end_position=match.source_end_position,
            )
        )

    return ReportOut(
        id=report.id,
        document_id=report.document_id,
        document_title=report.document.title,
        status=report.status,
        global_similarity_score=report.global_similarity_score,
        literal_similarity_score=report.literal_similarity_score,
        near_literal_similarity_score=report.near_literal_similarity_score,
        similarity_excluding_references_score=report.similarity_excluding_references_score,
        section_similarity=report.section_similarity or {},
        source_summary=source_summary,
        warnings=report.warnings or [],
        exclude_references=report.exclude_references,
        created_at=report.created_at,
        completed_at=report.completed_at,
        matches=match_payloads,
    )
