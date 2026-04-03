from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for batch subtitle extraction."""
    parser = argparse.ArgumentParser(
        description="Download YouTube subtitles in batch and save them as plain text files.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("urls.txt"),
        help="Text file with one YouTube URL per line.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where .txt files will be written.",
    )
    parser.add_argument(
        "-l",
        "--languages",
        default="ru,en",
        help="Comma-separated language priority, for example: ru,en,uk.",
    )
    parser.add_argument(
        "--prefer-auto",
        action="store_true",
        help="Prefer auto-generated captions over manual subtitles.",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Path to a Netscape/Mozilla cookies.txt file.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser name for yt-dlp cookie extraction, for example: chrome or firefox.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="HTTP User-Agent string to use for YouTube requests.",
    )
    parser.add_argument(
        "--sleep-between-videos",
        type=float,
        default=0.0,
        help="Optional delay in seconds between processing videos.",
    )
    return parser.parse_args()


def read_urls(path: Path) -> list[str]:
    """Load unique, non-comment URLs from the input file."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    urls: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            urls.append(line)
    return urls
