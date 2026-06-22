from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.core.config import settings
from app.services.text_processing import tokenize_words


@dataclass(frozen=True)
class Fingerprint:
    hash_value: str
    position: int


def hash_kgram(kgram: str) -> str:
    digest = hashlib.blake2b(kgram.encode("utf-8"), digest_size=8).hexdigest()
    return digest


def word_kgrams(text: str, k: int | None = None) -> list[tuple[str, int]]:
    k = k or settings.WINNOW_K_GRAM_SIZE
    words = tokenize_words(text)
    if len(words) < k:
        return []
    return [(" ".join(words[index : index + k]), index) for index in range(0, len(words) - k + 1)]


def hashed_kgrams(text: str, k: int | None = None) -> list[Fingerprint]:
    return [Fingerprint(hash_kgram(kgram), position) for kgram, position in word_kgrams(text, k)]


def winnow(hashes: list[Fingerprint], window_size: int | None = None) -> list[Fingerprint]:
    window_size = window_size or settings.WINNOW_WINDOW_SIZE
    if not hashes:
        return []

    selected: list[Fingerprint] = []
    seen: set[tuple[str, int]] = set()

    if len(hashes) <= window_size:
        chosen = min(hashes, key=lambda item: int(item.hash_value, 16))
        return [chosen]

    for start in range(0, len(hashes) - window_size + 1):
        window = hashes[start : start + window_size]
        min_hash = min(int(item.hash_value, 16) for item in window)
        tied = [item for item in window if int(item.hash_value, 16) == min_hash]
        chosen = tied[-1]
        key = (chosen.hash_value, chosen.position)
        if key not in seen:
            selected.append(chosen)
            seen.add(key)

    return selected


def fingerprint_text(
    text: str,
    k: int | None = None,
    window_size: int | None = None,
) -> list[Fingerprint]:
    return winnow(hashed_kgrams(text, k), window_size)
