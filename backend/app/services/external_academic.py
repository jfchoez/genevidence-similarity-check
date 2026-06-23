from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.fingerprinting import fingerprint_text
from app.services.text_processing import TextCleaner, tokenize_words


TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")

STOPWORDS = {
    "a",
    "al",
    "and",
    "ante",
    "as",
    "con",
    "de",
    "del",
    "el",
    "en",
    "entre",
    "es",
    "estudio",
    "fue",
    "for",
    "from",
    "in",
    "la",
    "las",
    "los",
    "of",
    "on",
    "or",
    "para",
    "por",
    "que",
    "se",
    "the",
    "to",
    "un",
    "una",
    "was",
    "were",
    "with",
    "y",
}


@dataclass(frozen=True)
class ExternalAcademicSource:
    provider: str
    source_id: str
    title: str
    url: str | None
    text: str
    year: int | None = None
    doi: str | None = None


@dataclass(frozen=True)
class ExternalTextChunk:
    text: str
    normalized_text: str
    fingerprint_hashes: list[str]
    word_count: int
    start_position: int = 0
    end_position: int = 0


class ExternalAcademicSearchService:
    """Searches academic open metadata APIs for externally comparable text."""

    def representative_queries(self, chunks: list[Any]) -> list[str]:
        queries: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            if getattr(chunk, "word_count", 0) < settings.EXTERNAL_ACADEMIC_MIN_QUERY_WORDS:
                continue
            query = self._query_from_text(getattr(chunk, "text", ""))
            key = TextCleaner.normalized(query)
            if query and key not in seen:
                queries.append(query)
                seen.add(key)
            if len(queries) >= settings.EXTERNAL_ACADEMIC_MAX_QUERIES:
                break
        return queries

    def search_for_chunks(self, chunks: list[Any]) -> list[ExternalAcademicSource]:
        return self.search(self.representative_queries(chunks))

    def search(self, queries: list[str]) -> list[ExternalAcademicSource]:
        sources: list[ExternalAcademicSource] = []
        seen: set[str] = set()
        providers_raw = settings.EXTERNAL_ACADEMIC_PROVIDERS
        providers = (
            {item.strip().lower() for item in providers_raw.split(",") if item.strip()}
            if isinstance(providers_raw, str)
            else set(providers_raw)
        )

        for query in queries:
            query_sources: list[ExternalAcademicSource] = []
            if "europepmc" in providers:
                query_sources.extend(self._search_europe_pmc(query))
            if "crossref" in providers:
                query_sources.extend(self._search_crossref(query))
            if "openalex" in providers and settings.OPENALEX_API_KEY:
                query_sources.extend(self._search_openalex(query))

            for source in query_sources:
                if len(tokenize_words(source.text)) < 20:
                    continue
                key = self._dedupe_key(source)
                if key in seen:
                    continue
                seen.add(key)
                sources.append(source)
                if len(sources) >= settings.EXTERNAL_ACADEMIC_MAX_SOURCES:
                    return sources

        return sources

    def source_as_chunk(self, source: ExternalAcademicSource) -> ExternalTextChunk:
        fingerprints = fingerprint_text(source.text)
        return ExternalTextChunk(
            text=source.text,
            normalized_text=TextCleaner.normalized(source.text),
            fingerprint_hashes=[fingerprint.hash_value for fingerprint in fingerprints],
            word_count=len(tokenize_words(source.text)),
            end_position=len(source.text),
        )

    def _search_europe_pmc(self, query: str) -> list[ExternalAcademicSource]:
        params = urlencode(
            {
                "query": query,
                "format": "json",
                "resultType": "core",
                "pageSize": settings.EXTERNAL_ACADEMIC_RESULTS_PER_QUERY,
            }
        )
        payload = self._get_json(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}")
        results = payload.get("resultList", {}).get("result", []) if isinstance(payload, dict) else []
        sources: list[ExternalAcademicSource] = []
        for item in results:
            title = self._clean_text(item.get("title"))
            abstract = self._clean_text(item.get("abstractText"))
            if not title and not abstract:
                continue
            source = self._clean_text(item.get("source")) or "EuropePMC"
            identifier = self._clean_text(item.get("pmcid") or item.get("pmid") or item.get("id")) or title
            doi = self._clean_text(item.get("doi")) or None
            url = f"https://europepmc.org/article/{source}/{identifier}" if identifier else None
            sources.append(
                ExternalAcademicSource(
                    provider="Europe PMC",
                    source_id=f"europepmc:{identifier}",
                    title=title or "Europe PMC record",
                    url=url,
                    text=self._join_title_abstract(title, abstract),
                    year=self._safe_year(item.get("pubYear")),
                    doi=doi,
                )
            )
        return sources

    def _search_crossref(self, query: str) -> list[ExternalAcademicSource]:
        params = urlencode(
            {
                "query.bibliographic": query,
                "rows": settings.EXTERNAL_ACADEMIC_RESULTS_PER_QUERY,
            }
        )
        payload = self._get_json(f"https://api.crossref.org/works?{params}")
        items = payload.get("message", {}).get("items", []) if isinstance(payload, dict) else []
        sources: list[ExternalAcademicSource] = []
        for item in items:
            title = self._clean_text(self._first(item.get("title")))
            abstract = self._clean_text(item.get("abstract"))
            if not title and not abstract:
                continue
            doi = self._clean_text(item.get("DOI")) or None
            url = self._clean_text(item.get("URL")) or (f"https://doi.org/{doi}" if doi else None)
            source_id = doi or url or title
            sources.append(
                ExternalAcademicSource(
                    provider="Crossref",
                    source_id=f"crossref:{source_id}",
                    title=title or "Crossref record",
                    url=url,
                    text=self._join_title_abstract(title, abstract),
                    year=self._crossref_year(item),
                    doi=doi,
                )
            )
        return sources

    def _search_openalex(self, query: str) -> list[ExternalAcademicSource]:
        params: dict[str, Any] = {
            "search": query,
            "per-page": settings.EXTERNAL_ACADEMIC_RESULTS_PER_QUERY,
            "filter": "has_abstract:true",
        }
        if settings.OPENALEX_API_KEY:
            params["api_key"] = settings.OPENALEX_API_KEY
        payload = self._get_json(f"https://api.openalex.org/works?{urlencode(params)}")
        results = payload.get("results", []) if isinstance(payload, dict) else []
        sources: list[ExternalAcademicSource] = []
        for item in results:
            title = self._clean_text(item.get("display_name"))
            abstract = self._openalex_abstract(item.get("abstract_inverted_index"))
            if not title and not abstract:
                continue
            doi = self._clean_text(item.get("doi")) or None
            url = self._openalex_url(item, doi)
            source_id = self._clean_text(item.get("id")) or doi or title
            sources.append(
                ExternalAcademicSource(
                    provider="OpenAlex",
                    source_id=f"openalex:{source_id}",
                    title=title or "OpenAlex work",
                    url=url,
                    text=self._join_title_abstract(title, abstract),
                    year=self._safe_year(item.get("publication_year")),
                    doi=doi,
                )
            )
        return sources

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": settings.EXTERNAL_ACADEMIC_USER_AGENT})
        try:
            with urlopen(request, timeout=settings.EXTERNAL_ACADEMIC_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

    @staticmethod
    def _query_from_text(text: str) -> str:
        candidates = [sentence.strip() for sentence in SENTENCE_RE.split(text) if sentence.strip()]
        candidates.append(text)
        for candidate in candidates:
            words = tokenize_words(candidate)
            content_words = [word for word in words if len(word) > 3 and word not in STOPWORDS]
            if len(words) >= 12 and len(content_words) >= 7:
                return " ".join(candidate.split())[:220]
        words = text.split()
        return " ".join(words[:28])[:220]

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            value = " ".join(str(item) for item in value if item)
        value = html.unescape(str(value))
        value = TAG_RE.sub(" ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @staticmethod
    def _join_title_abstract(title: str, abstract: str) -> str:
        return "\n\n".join(part for part in [title, abstract] if part)

    @staticmethod
    def _first(value: Any) -> Any:
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @staticmethod
    def _safe_year(value: Any) -> int | None:
        try:
            return int(str(value)[:4])
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _crossref_year(item: dict[str, Any]) -> int | None:
        for key in ("published-print", "published-online", "published", "created"):
            date_parts = item.get(key, {}).get("date-parts")
            if date_parts and date_parts[0]:
                return ExternalAcademicSearchService._safe_year(date_parts[0][0])
        return None

    @staticmethod
    def _openalex_abstract(inverted_index: Any) -> str:
        if not isinstance(inverted_index, dict):
            return ""
        positioned: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            if not isinstance(positions, list):
                continue
            for position in positions:
                try:
                    positioned.append((int(position), str(word)))
                except (TypeError, ValueError):
                    continue
        return " ".join(word for _, word in sorted(positioned))

    @staticmethod
    def _openalex_url(item: dict[str, Any], doi: str | None) -> str | None:
        primary = item.get("primary_location") or {}
        for value in (
            primary.get("landing_page_url"),
            primary.get("pdf_url"),
            (item.get("open_access") or {}).get("oa_url"),
            item.get("id"),
            doi,
        ):
            cleaned = ExternalAcademicSearchService._clean_text(value)
            if cleaned:
                return cleaned
        return None

    @staticmethod
    def _dedupe_key(source: ExternalAcademicSource) -> str:
        if source.doi:
            return f"doi:{source.doi.lower()}"
        if source.url:
            return f"url:{source.url.lower()}"
        return source.source_id.lower()
