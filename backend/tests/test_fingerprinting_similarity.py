from app.models import TextChunk
from app.services.fingerprinting import fingerprint_text, word_kgrams
from app.services.similarity import SimilarityEngine, jaccard_similarity


def chunk(text: str) -> TextChunk:
    fingerprints = fingerprint_text(text, k=5, window_size=4)
    return TextChunk(
        document_id=1,
        chunk_index=0,
        text=text,
        normalized_text=text.lower(),
        fingerprint_hashes=[fp.hash_value for fp in fingerprints],
        word_count=len(text.split()),
        start_position=0,
        end_position=len(text),
    )


def test_kgrams_and_fingerprints_are_generated():
    text = "uno dos tres cuatro cinco seis siete ocho nueve diez"
    assert len(word_kgrams(text, k=5)) == 6
    fingerprints = fingerprint_text(text, k=5, window_size=4)
    assert fingerprints
    assert all(fp.hash_value for fp in fingerprints)


def test_jaccard_detects_copied_text():
    left = chunk(" ".join(["gen"] * 5 + ["metodo", "resultado", "biomedico"] * 20))
    right = chunk(" ".join(["gen"] * 5 + ["metodo", "resultado", "biomedico"] * 20))
    assert jaccard_similarity(set(left.fingerprint_hashes), set(right.fingerprint_hashes)) == 1.0


def test_similarity_detects_minor_changes():
    left = chunk(
        "El estudio observacional analizo pacientes adultos con seguimiento clinico y resultados de laboratorio "
        "para estimar asociaciones entre variables metabolicas y desenlaces cardiovasculares."
    )
    right = chunk(
        "El estudio observacional evaluo pacientes adultos con seguimiento clinico y resultados de laboratorio "
        "para estimar asociaciones entre variables metabolicas y desenlaces cardiovasculares."
    )
    score = SimilarityEngine().score_pair(left, right, shared_fingerprint_count=3)
    assert score.match_type in {"near_exact", "partial", "exact"}


def test_similarity_ignores_unrelated_texts():
    left = chunk(" ".join("cardiologia metabolismo muestra clinica seguimiento".split() * 20))
    right = chunk(" ".join("astronomia telescopio galaxia orbita radiacion".split() * 20))
    score = SimilarityEngine().score_pair(left, right)
    assert score.match_type is None
