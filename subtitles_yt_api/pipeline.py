from __future__ import annotations

import sys
import time
from pathlib import Path

from yt_dlp import YoutubeDL

from subtitles_yt_api.cli import parse_args, read_urls
from subtitles_yt_api.rendering import build_output_text, sanitize_filename
from subtitles_yt_api.subtitle_parsers import parse_subtitle_bytes
from subtitles_yt_api.youtube_client import (
    build_ydl_opts,
    extract_preferred_language,
    fetch_track_bytes,
    is_rate_limited,
    rate_limit_hint,
    select_track,
)

RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2
RATE_LIMIT_DELAY_SECONDS = 20


def process_video(
    url: str,
    output_dir: Path,
    preferred_languages: list[str],
    prefer_auto: bool,
    cookies_file: Path | None,
    cookies_from_browser: str | None,
    user_agent: str,
) -> tuple[bool, str]:
    """Run the full subtitle extraction pipeline for a single YouTube URL."""
    last_error: Exception | None = None
    video_label = url

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            ydl_opts = build_ydl_opts(
                cookies_file=cookies_file,
                cookies_from_browser=cookies_from_browser,
                user_agent=user_agent,
            )
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False, process=False)

                title = info.get("title") or info.get("id") or "video"
                video_id = info.get("id") or "unknown"
                video_label = video_id
                channel = info.get("channel") or info.get("uploader") or ""

                manual_tracks = info.get("subtitles") or {}
                auto_tracks = info.get("automatic_captions") or {}
                source_priority = (
                    (("auto", auto_tracks), ("subtitles", manual_tracks))
                    if prefer_auto
                    else (("subtitles", manual_tracks), ("auto", auto_tracks))
                )

                selected_source = None
                selected_language = None
                selected_formats = None

                for source_name, tracks in source_priority:
                    match = extract_preferred_language(tracks, preferred_languages)
                    if match:
                        selected_language, selected_formats = match
                        selected_source = source_name
                        break

                if not selected_formats or not selected_language or not selected_source:
                    return False, f"{video_id}: subtitles not found"

                chosen_track = select_track(selected_formats)
                if not chosen_track:
                    return False, f"{video_id}: subtitle track has no downloadable URL"

                payload = fetch_track_bytes(ydl, chosen_track["url"])
                ext = chosen_track.get("ext") or "txt"
                transcript = parse_subtitle_bytes(payload, ext)
                if not transcript.strip():
                    return False, f"{video_id}: subtitle track was empty after parsing"

                safe_title = sanitize_filename(title)
                output_path = output_dir / f"{video_id}_{safe_title}.txt"
                output_text = build_output_text(
                    title=title,
                    url=url,
                    channel=channel,
                    language=selected_language,
                    source_label=selected_source,
                    transcript=transcript,
                )
                output_path.write_text(output_text, encoding="utf-8")
                return True, f"{video_id}: saved {output_path.name}"
        except Exception as exc:
            last_error = exc
            if attempt == RETRY_ATTEMPTS:
                break
            delay = RATE_LIMIT_DELAY_SECONDS if is_rate_limited(exc) else RETRY_DELAY_SECONDS
            time.sleep(delay)

    if last_error and is_rate_limited(last_error):
        hint = rate_limit_hint(cookies_file, cookies_from_browser)
        return False, f"{video_label}: failed after {RETRY_ATTEMPTS} attempts: {hint}"

    return False, f"{video_label}: failed after {RETRY_ATTEMPTS} attempts: {last_error}"


def main() -> int:
    """Entrypoint for batch processing and per-video progress reporting."""
    args = parse_args()
    preferred_languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    urls = read_urls(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not urls:
        print(f"No URLs found in {args.input}", file=sys.stderr)
        return 1

    failures = 0
    for index, url in enumerate(urls, start=1):
        try:
            ok, message = process_video(
                url=url,
                output_dir=args.output_dir,
                preferred_languages=preferred_languages,
                prefer_auto=args.prefer_auto,
                cookies_file=args.cookies,
                cookies_from_browser=args.cookies_from_browser,
                user_agent=args.user_agent,
            )
        except Exception as exc:
            ok = False
            message = f"{url}: {exc}"

        prefix = "[OK]" if ok else "[FAIL]"
        print(f"{prefix} {index}/{len(urls)} {message}")
        if not ok:
            failures += 1

        if args.sleep_between_videos > 0 and index < len(urls):
            time.sleep(args.sleep_between_videos)

    return 1 if failures else 0
