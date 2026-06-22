from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import ChunkFingerprint, Document, DocumentSection, DocumentStatus, TextChunk
from app.services.embeddings import SemanticSimilarityService
from app.services.extractor import DocumentTextExtractor
from app.services.fingerprinting import fingerprint_text
from app.services.text_processing import SectionDetector, TextCleaner, TextSegmenter, tokenize_words


def process_document_task(document_id: int) -> None:
    with SessionLocal() as db:
        process_document(db, document_id)


def process_document(db: Session, document_id: int) -> None:
    document = db.get(Document, document_id)
    if not document:
        return

    try:
        document.status = DocumentStatus.processing.value
        document.error_message = None
        db.commit()

        extracted = DocumentTextExtractor().extract(document.storage_path, document.file_type)
        if not extracted or len(tokenize_words(extracted)) == 0:
            raise ValueError("Document is empty or text could not be extracted")

        cleaned = TextCleaner.clean(extracted)
        document.extracted_text = extracted
        document.cleaned_text = cleaned
        document.word_count = len(tokenize_words(cleaned))

        document.sections.clear()
        document.chunks.clear()
        db.flush()

        section_spans = SectionDetector.detect(cleaned)
        section_rows: dict[str, DocumentSection] = {}
        ordered_sections: list[DocumentSection] = []
        for span in section_spans:
            section = DocumentSection(
                document_id=document.id,
                section_name=span.section_name,
                start_position=span.start_position,
                end_position=span.end_position,
                text=span.text,
            )
            db.add(section)
            ordered_sections.append(section)
        db.flush()
        for section in ordered_sections:
            section_rows[f"{section.section_name}:{section.start_position}:{section.end_position}"] = section

        chunks_to_embed: list[TextChunk] = []
        chunk_drafts = TextSegmenter().segment(cleaned, section_spans)
        for draft in chunk_drafts:
            section = _find_section_for_draft(draft.section_name, draft.start_position, ordered_sections)
            fingerprints = fingerprint_text(draft.normalized_text)
            chunk = TextChunk(
                document_id=document.id,
                section_id=section.id if section else None,
                chunk_index=draft.chunk_index,
                text=draft.text,
                normalized_text=draft.normalized_text,
                fingerprint_hashes=[fp.hash_value for fp in fingerprints],
                word_count=draft.word_count,
                start_position=draft.start_position,
                end_position=draft.end_position,
            )
            db.add(chunk)
            db.flush()
            for fp in fingerprints:
                db.add(ChunkFingerprint(chunk_id=chunk.id, hash_value=fp.hash_value, position=fp.position))
            chunks_to_embed.append(chunk)

        SemanticSimilarityService().store_embeddings(db, chunks_to_embed)
        document.status = DocumentStatus.indexed.value
        db.commit()
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document:
            document.status = DocumentStatus.failed.value
            document.error_message = str(exc)
            db.commit()


def _find_section_for_draft(
    section_name: str,
    start_position: int,
    sections: list[DocumentSection],
) -> DocumentSection | None:
    candidates = [section for section in sections if section.section_name == section_name]
    if not candidates:
        return None
    return min(candidates, key=lambda section: abs(section.start_position - start_position))
