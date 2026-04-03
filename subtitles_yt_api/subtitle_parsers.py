from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

from subtitles_yt_api.text_utils import merge_chunks, normalize_whitespace


def parse_vtt(payload: bytes) -> str:
    """Parse a WebVTT subtitle file into normalized plain text."""
    text = payload.decode("utf-8", errors="replace")
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    chunks: list[str] = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0] == "WEBVTT":
            continue
        if lines[0].startswith("NOTE") or lines[0].startswith("STYLE"):
            continue

        cleaned: list[str] = []
        for line in lines:
            if re.match(r"^\d+$", line):
                continue
            if "-->" in line:
                continue
            cleaned.append(line)

        if cleaned:
            chunks.append(" ".join(cleaned))

    return merge_chunks(chunks)


def parse_json3(payload: bytes) -> str:
    """Parse YouTube json3 captions into normalized plain text."""
    document = json.loads(payload.decode("utf-8", errors="replace"))
    chunks: list[str] = []

    for event in document.get("events", []):
        segments = event.get("segs") or []
        text = "".join(segment.get("utf8", "") for segment in segments)
        if text.strip():
            chunks.append(text)

    return merge_chunks(chunks)


def parse_ttml(payload: bytes) -> str:
    """Parse TTML/SRV XML captions into normalized plain text."""
    root = ET.fromstring(payload)
    chunks: list[str] = []

    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in {"p", "span"}:
            continue
        text = "".join(element.itertext())
        if text.strip():
            chunks.append(text)

    return merge_chunks(chunks)


def parse_subtitle_bytes(payload: bytes, ext: str) -> str:
    """Dispatch raw subtitle bytes to the parser that matches the subtitle format."""
    if ext == "vtt":
        return parse_vtt(payload)
    if ext == "json3":
        return parse_json3(payload)
    if ext in {"ttml", "srv1", "srv2", "srv3"}:
        return parse_ttml(payload)
    return normalize_whitespace(payload.decode("utf-8", errors="replace"))
