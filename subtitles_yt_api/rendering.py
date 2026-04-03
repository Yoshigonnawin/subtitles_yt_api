from __future__ import annotations

from subtitles_yt_api.text_utils import sanitize_filename


def build_output_text(
    *,
    title: str,
    url: str,
    channel: str,
    language: str,
    source_label: str,
    transcript: str,
) -> str:
    """Render the final text file with a small metadata header and transcript body."""
    header = [
        f"Title: {title}",
        f"URL: {url}",
        f"Channel: {channel or 'unknown'}",
        f"Language: {language}",
        f"Source: {source_label}",
        "",
    ]
    return "\n".join(header) + transcript.strip() + "\n"


__all__ = ["build_output_text", "sanitize_filename"]
