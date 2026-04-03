from __future__ import annotations

import urllib.error
from pathlib import Path

from yt_dlp import YoutubeDL

FORMAT_PREFERENCE = ("vtt", "srv3", "json3", "ttml", "srv2", "srv1")


def extract_preferred_language(
    tracks: dict[str, list[dict]],
    preferred_languages: list[str],
) -> tuple[str, list[dict]] | None:
    """Choose the best subtitle language entry based on language priority."""
    if not tracks:
        return None

    for preferred in preferred_languages:
        preferred = preferred.strip()
        if not preferred:
            continue

        exact = tracks.get(preferred)
        if exact:
            return preferred, exact

        base = preferred.split("-", 1)[0]
        for language_code, formats in tracks.items():
            if language_code == preferred or language_code.startswith(f"{base}-"):
                return language_code, formats

    return next(iter(tracks.items()), None)


def select_track(formats: list[dict]) -> dict | None:
    """Choose the most convenient subtitle track format for downstream parsing."""
    for wanted_ext in FORMAT_PREFERENCE:
        for track in formats:
            if track.get("ext") == wanted_ext and track.get("url"):
                return track
    for track in formats:
        if track.get("url"):
            return track
    return None


def build_ydl_opts(
    *,
    cookies_file: Path | None,
    cookies_from_browser: str | None,
    user_agent: str,
) -> dict:
    """Build yt-dlp options shared by metadata lookup and subtitle download."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreconfig": True,
        "http_headers": {"User-Agent": user_agent},
    }
    if cookies_file:
        opts["cookiefile"] = str(cookies_file)
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = cookies_from_browser
    return opts


def fetch_track_bytes(ydl: YoutubeDL, url: str) -> bytes:
    """Download subtitle bytes through yt-dlp so cookies and headers are reused."""
    with ydl.urlopen(url) as response:
        return response.read()


def is_rate_limited(exc: Exception) -> bool:
    """Detect whether an exception looks like a YouTube HTTP 429 rate limit."""
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
        return True
    return "429" in str(exc)


def rate_limit_hint(cookies_file: Path | None, cookies_from_browser: str | None) -> str:
    """Build a user-facing hint for recovering from temporary YouTube rate limits."""
    hints = [
        "YouTube returned HTTP 429",
        "open the video in your browser and refresh the page first",
    ]
    if not cookies_from_browser and not cookies_file:
        hints.append("then run with --cookies-from-browser <browser> or --cookies <cookies.txt>")
    hints.append("if the block is fresh, wait 10-30 minutes and try again")
    return "; ".join(hints)
