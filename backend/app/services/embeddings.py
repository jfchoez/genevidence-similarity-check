from __future__ import annotations

import math
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ChunkEmbedding, TextChunk


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def should_mark_possible_paraphrase(
    cosine_score: float,
    fuzzy_score: float,
    target_word_count: int,
) -> bool:
    return (
        cosine_score >= settings.SEMANTIC_COSINE_THRESHOLD
        and fuzzy_score < 75
        and target_word_count >= settings.SEMANTIC_MIN_WORDS
    )


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.SEMANTIC_MODEL_NAME)


class SemanticSimilarityService:
    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = settings.SEMANTIC_ENABLED if enabled is None else enabled

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.enabled or not texts:
            return []
        model = _load_model()
        prefixed = [self._prefix(text_value) for text_value in texts]
        vectors = model.encode(prefixed, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def store_embeddings(self, db: Session, chunks: list[TextChunk]) -> None:
        if not self.enabled or not chunks:
            return
        vectors = self.embed_texts([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, vectors):
            db.add(
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    model_name=settings.SEMANTIC_MODEL_NAME,
                    dimensions=settings.SEMANTIC_EMBEDDING_DIMENSIONS,
                    embedding=vector,
                )
            )

    def semantic_candidates(
        self,
        db: Session,
        target_chunk: TextChunk,
        target_document_id: int,
        exclude_chunk_pairs: set[tuple[int, int]],
    ) -> list[tuple[int, float]]:
        if not self.enabled or not target_chunk.embedding:
            return []
        if not db.bind or db.bind.dialect.name != "postgresql":
            return []

        vector_value = "[" + ",".join(str(value) for value in target_chunk.embedding.embedding) + "]"
        rows = db.execute(
            text(
                """
                SELECT ce.chunk_id, 1 - (ce.embedding <=> CAST(:vector AS vector)) AS cosine_score
                FROM chunk_embeddings ce
                JOIN text_chunks tc ON tc.id = ce.chunk_id
                JOIN documents d ON d.id = tc.document_id
                WHERE tc.document_id != :target_document_id
                  AND tc.word_count >= :min_words
                  AND d.status = 'indexed'
                ORDER BY ce.embedding <=> CAST(:vector AS vector)
                LIMIT :limit
                """
            ),
            {
                "vector": vector_value,
                "target_document_id": target_document_id,
                "min_words": settings.SEMANTIC_MIN_WORDS,
                "limit": settings.SEMANTIC_MAX_CANDIDATES,
            },
        ).all()
        return [
            (int(row.chunk_id), float(row.cosine_score))
            for row in rows
            if (target_chunk.id, int(row.chunk_id)) not in exclude_chunk_pairs
        ]

    @staticmethod
    def _prefix(text_value: str) -> str:
        if settings.SEMANTIC_MODEL_NAME.startswith("intfloat/multilingual-e5"):
            return f"passage: {text_value}"
        return text_value
