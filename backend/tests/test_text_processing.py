from app.services.text_processing import SectionDetector, TextCleaner, TextSegmenter, find_common_method_phrases


def test_text_cleaner_normalizes_spaces():
    text = "Resumen\r\n\r\n\r\nEste   es\tun texto."
    assert TextCleaner.clean(text) == "Resumen\n\nEste es un texto."


def test_segmenter_creates_overlapping_chunks():
    text = " ".join(f"palabra{i}" for i in range(40))
    sections = SectionDetector.detect(text)
    chunks = TextSegmenter(chunk_size_words=20, overlap_words=5).segment(text, sections)
    assert len(chunks) == 3
    assert chunks[0].word_count == 20
    assert chunks[1].start_position < chunks[0].end_position


def test_section_detector_classifies_references():
    text = "Introduccion\nTexto inicial.\nReferencias\nAutor 2024."
    sections = SectionDetector.detect(text)
    assert [section.section_name for section in sections] == ["introduccion", "referencias"]


def test_common_method_phrase_is_marked():
    labels = find_common_method_phrases("Se realizo un analisis descriptivo de la muestra.")
    assert "se realizo un analisis descriptivo" in labels
