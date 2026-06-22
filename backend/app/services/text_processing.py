from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.core.common_phrases import COMMON_METHOD_PHRASES
from app.core.config import settings


WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
SPACE_RE = re.compile(r"[ \t\r\f\v]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_for_matching(value: str) -> str:
    value = strip_accents(value).lower()
    value = re.sub(r"[^\w\s%]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def tokenize_words(value: str) -> list[str]:
    return WORD_RE.findall(normalize_for_matching(value))


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        text = text.replace("\x00", " ")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = SPACE_RE.sub(" ", text)
        text = MULTI_NEWLINE_RE.sub("\n\n", text)
        return text.strip()

    @staticmethod
    def normalized(text: str) -> str:
        return normalize_for_matching(text)


@dataclass(frozen=True)
class SectionSpan:
    section_name: str
    start_position: int
    end_position: int
    text: str


SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "resumen": ("resumen", "abstract"),
    "introduccion": ("introduccion", "introduccion general"),
    "antecedentes": ("antecedentes", "marco teorico", "revision de literatura"),
    "metodologia": ("metodologia", "metodos", "materiales y metodos", "pacientes y metodos"),
    "resultados": ("resultados",),
    "discusion": ("discusion", "discusion y conclusiones"),
    "referencias": ("referencias", "bibliografia", "literatura citada"),
    "anexos": ("anexos", "apendices", "apendice"),
}


def canonical_section_name(raw_heading: str) -> str | None:
    value = normalize_for_matching(raw_heading)
    value = re.sub(r"^\d+(\.\d+)*\s+", "", value)
    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if value == alias or value.startswith(f"{alias} "):
                return canonical
    return None


class SectionDetector:
    @staticmethod
    def detect(text: str) -> list[SectionSpan]:
        headings: list[tuple[str, int]] = []
        offset = 0
        for line in text.splitlines(keepends=True):
            stripped = line.strip(" \t\n:.-")
            if 0 < len(stripped) <= 80:
                section = canonical_section_name(stripped)
                if section:
                    headings.append((section, offset))
            offset += len(line)

        if not headings:
            return [
                SectionSpan(
                    section_name="seccion no detectada",
                    start_position=0,
                    end_position=len(text),
                    text=text,
                )
            ]

        spans: list[SectionSpan] = []
        for index, (name, start) in enumerate(headings):
            end = headings[index + 1][1] if index + 1 < len(headings) else len(text)
            spans.append(
                SectionSpan(
                    section_name=name,
                    start_position=start,
                    end_position=end,
                    text=text[start:end].strip(),
                )
            )
        return spans


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    text: str
    normalized_text: str
    word_count: int
    start_position: int
    end_position: int
    section_name: str


class TextSegmenter:
    def __init__(
        self,
        chunk_size_words: int | None = None,
        overlap_words: int | None = None,
    ) -> None:
        self.chunk_size_words = chunk_size_words or settings.CHUNK_SIZE_WORDS
        self.overlap_words = overlap_words or settings.CHUNK_OVERLAP_WORDS

    def segment(self, text: str, sections: list[SectionSpan]) -> list[ChunkDraft]:
        matches = list(re.finditer(r"\S+", text))
        if not matches:
            return []

        step = max(1, self.chunk_size_words - self.overlap_words)
        chunks: list[ChunkDraft] = []

        for chunk_index, start_word in enumerate(range(0, len(matches), step)):
            end_word = min(start_word + self.chunk_size_words, len(matches))
            start_position = matches[start_word].start()
            end_position = matches[end_word - 1].end()
            chunk_text = text[start_position:end_position].strip()
            section_name = self._section_for_range(start_position, end_position, sections)
            chunks.append(
                ChunkDraft(
                    chunk_index=chunk_index,
                    text=chunk_text,
                    normalized_text=TextCleaner.normalized(chunk_text),
                    word_count=end_word - start_word,
                    start_position=start_position,
                    end_position=end_position,
                    section_name=section_name,
                )
            )
            if end_word == len(matches):
                break

        return chunks

    @staticmethod
    def _section_for_range(start: int, end: int, sections: list[SectionSpan]) -> str:
        best_name = "seccion no detectada"
        best_overlap = 0
        for section in sections:
            overlap = max(0, min(end, section.end_position) - max(start, section.start_position))
            if overlap > best_overlap:
                best_overlap = overlap
                best_name = section.section_name
        return best_name


def find_common_method_phrases(text: str) -> list[str]:
    normalized = normalize_for_matching(text)
    matches: list[str] = []
    for phrase in COMMON_METHOD_PHRASES:
        if normalize_for_matching(phrase) in normalized:
            matches.append(phrase)
    return matches
