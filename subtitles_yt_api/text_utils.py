from __future__ import annotations

import html
import re
from typing import Iterable


def sanitize_filename(value: str) -> str:
    """Convert a video title into a filesystem-safe output filename."""
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r'[\\/:*?"<>|]+', "_", value)
    value = value.replace("\n", " ").replace("\r", " ")
    return value[:120].strip(" ._") or "video"


def normalize_whitespace(value: str) -> str:
    """Collapse markup, entities, and repeated whitespace into readable text."""
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def overlap_length(left: str, right: str, minimum: int = 8) -> int:
    """Return the shared overlap length between the end of left and start of right."""
    max_size = min(len(left), len(right))
    for size in range(max_size, minimum - 1, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def merge_chunks(chunks: Iterable[str]) -> str:
    """Merge caption chunks while removing obvious duplicates and overlaps."""
    merged: list[str] = []

    for chunk in chunks:
        text = normalize_whitespace(chunk)
        if not text:
            continue

        if not merged:
            merged.append(text)
            continue

        previous = merged[-1]
        if text == previous:
            continue
        if len(text) <= len(previous) and text in previous:
            continue
        if text.startswith(previous):
            suffix = text[len(previous) :].strip()
            if suffix:
                merged[-1] = f"{previous} {suffix}".strip()
            continue

        shared = overlap_length(previous, text)
        if shared:
            suffix = text[shared:].strip()
            if suffix:
                merged[-1] = f"{previous} {suffix}".strip()
            continue

        merged.append(text)

    return "\n".join(merged)
