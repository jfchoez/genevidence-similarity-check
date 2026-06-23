from app.models import TextChunk
from app.services.external_academic import ExternalAcademicSearchService, ExternalAcademicSource
from app.services.fingerprinting import fingerprint_text
from app.services.reporting import ReportGenerator
from app.services.text_processing import TextCleaner


def chunk(text: str, chunk_id: int = 1) -> TextChunk:
    fingerprints = fingerprint_text(text)
    return TextChunk(
        id=chunk_id,
        document_id=1,
        chunk_index=0,
        text=text,
        normalized_text=TextCleaner.normalized(text),
        fingerprint_hashes=[fingerprint.hash_value for fingerprint in fingerprints],
        word_count=len(text.split()),
        start_position=0,
        end_position=len(text),
    )


class FakeExternalSearch:
    def __init__(self, source: ExternalAcademicSource) -> None:
        self.source = source
        self.real_service = ExternalAcademicSearchService()

    def search_for_chunks(self, chunks):
        return [self.source]

    def source_as_chunk(self, source):
        return self.real_service.source_as_chunk(source)


def source(text: str) -> ExternalAcademicSource:
    return ExternalAcademicSource(
        provider="Europe PMC",
        source_id="europepmc:test-1",
        title="Evaluacion clinica de biomarcadores",
        url="https://europepmc.org/article/MED/test-1",
        text=text,
        year=2024,
        doi="10.0000/example",
    )


def repeated_text(base: str) -> str:
    return " ".join([base] * 18)


def test_representative_queries_uses_informative_chunk_text():
    text = (
        "La evaluacion de biomarcadores inflamatorios en pacientes adultos con seguimiento clinico "
        "permite estimar asociaciones entre exposicion metabolica, respuesta terapeutica y desenlaces "
        "cardiovasculares reportados durante la fase de observacion. El protocolo incluyo mediciones "
        "basales, controles de calidad de laboratorio y seguimiento longitudinal de eventos clinicos."
    )
    queries = ExternalAcademicSearchService().representative_queries([chunk(text)])
    assert queries
    assert "biomarcadores inflamatorios" in queries[0]


def test_external_academic_match_detects_copied_text():
    text = repeated_text(
        "La evaluacion de biomarcadores inflamatorios en pacientes adultos con seguimiento clinico "
        "permitio estimar asociaciones entre exposicion metabolica y desenlaces cardiovasculares"
    )
    generator = ReportGenerator(db=None)  # type: ignore[arg-type]
    generator.external_academic = FakeExternalSearch(source(text))  # type: ignore[assignment]

    matches = generator._external_academic_matches(1, [chunk(text)])

    assert len(matches) == 1
    assert matches[0].source_kind == "external_academic"
    assert matches[0].match_type in {"exact", "near_exact", "partial"}
    assert matches[0].similarity_score >= 90


def test_external_academic_match_detects_minor_changes():
    target = repeated_text(
        "La evaluacion de biomarcadores inflamatorios en pacientes adultos con seguimiento clinico "
        "permitio estimar asociaciones entre exposicion metabolica y desenlaces cardiovasculares"
    )
    external = repeated_text(
        "La evaluacion de biomarcadores inflamatorios en pacientes adultos con vigilancia clinica "
        "permitio calcular asociaciones entre exposicion metabolica y desenlaces cardiovasculares"
    )
    generator = ReportGenerator(db=None)  # type: ignore[arg-type]
    generator.external_academic = FakeExternalSearch(source(external))  # type: ignore[assignment]

    matches = generator._external_academic_matches(1, [chunk(target)])

    assert len(matches) == 1
    assert matches[0].similarity_score >= 78


def test_external_academic_match_ignores_unrelated_text():
    target = repeated_text(
        "La evaluacion de biomarcadores inflamatorios en pacientes adultos con seguimiento clinico "
        "permitio estimar asociaciones entre exposicion metabolica y desenlaces cardiovasculares"
    )
    unrelated = repeated_text(
        "El analisis de imagenes astronomicas describio variaciones orbitales de cuerpos celestes "
        "mediante telescopios opticos y mediciones espectrales"
    )
    generator = ReportGenerator(db=None)  # type: ignore[arg-type]
    generator.external_academic = FakeExternalSearch(source(unrelated))  # type: ignore[assignment]

    matches = generator._external_academic_matches(1, [chunk(target)])

    assert matches == []
