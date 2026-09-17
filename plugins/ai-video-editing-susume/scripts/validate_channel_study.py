#!/usr/bin/env python3
"""Validate evidence records for studying an unfamiliar YouTube channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TEMPORAL_FIELDS = (
    "start",
    "end",
    "method",
    "evidence_ref",
    "before",
    "entry",
    "hold",
    "exit",
    "caption_interaction",
    "audio_status",
    "audio_notes",
)
METHODS = {
    "video_playback",
    "browser_playback",
    "frame_sequence",
    "decoded_video_frame",
    "native_project",
    "video_analysis",
}
AUDIO_STATES = {"listened", "placement_only", "unreviewed"}


def load_videos(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    videos = payload.get("videos") if isinstance(payload, dict) else payload
    if not isinstance(videos, list):
        raise ValueError("root must be an array or an object with a videos array")
    if any(not isinstance(video, dict) for video in videos):
        raise ValueError("every videos entry must be an object")
    return videos


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(
    videos: list[dict[str, Any]],
    minimum: int,
    channel_id: str | None,
    require_temporal: bool,
    require_full_watch: bool,
    require_audio: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    channels: set[str] = set()
    full_watch_count = 0
    audio_reviewed_count = 0
    temporal_count = 0

    for index, video in enumerate(videos):
        label = f"videos[{index}]"
        video_id = video.get("id")
        if not nonempty(video_id):
            errors.append(f"{label}.id is required")
        elif video_id in ids:
            errors.append(f"{label}.id duplicates {video_id}")
        else:
            ids.add(video_id)

        current_channel = video.get("channel_id")
        if not nonempty(current_channel):
            errors.append(f"{label}.channel_id is required")
        else:
            channels.add(current_channel)
            if channel_id and current_channel != channel_id:
                errors.append(f"{label}.channel_id must equal {channel_id}")

        for field in ("title", "url", "date"):
            if not nonempty(video.get(field)):
                errors.append(f"{label}.{field} is required")
        duration = video.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{label}.duration must be a positive number")
        if video.get("visual_reviewed") is not True:
            errors.append(f"{label}.visual_reviewed must be true after actual visual review")

        if video.get("full_watch") is True:
            full_watch_count += 1
        elif require_full_watch:
            errors.append(f"{label}.full_watch must be true for certification")

        if video.get("audio_reviewed") is True:
            audio_reviewed_count += 1
        elif require_audio:
            errors.append(f"{label}.audio_reviewed must be true for certification")

        reviews = video.get("temporal_reviews", [])
        if not isinstance(reviews, list):
            errors.append(f"{label}.temporal_reviews must be an array")
            continue
        temporal_count += len(reviews)
        if require_temporal and len(reviews) < 3:
            errors.append(f"{label}.temporal_reviews needs at least 3 entries")

        for review_index, review in enumerate(reviews):
            review_label = f"{label}.temporal_reviews[{review_index}]"
            if not isinstance(review, dict):
                errors.append(f"{review_label} must be an object")
                continue
            for field in TEMPORAL_FIELDS:
                if field not in review:
                    errors.append(f"{review_label}.{field} is required")
            start, end = review.get("start"), review.get("end")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end <= start:
                errors.append(f"{review_label} must have 0 <= start < end")
            if review.get("method") not in METHODS:
                errors.append(f"{review_label}.method is not supported")
            for field in ("evidence_ref", "before", "entry", "hold", "exit", "caption_interaction"):
                if not nonempty(review.get(field)):
                    errors.append(f"{review_label}.{field} must be non-empty")
            audio_status = review.get("audio_status")
            if audio_status not in AUDIO_STATES:
                errors.append(f"{review_label}.audio_status is not supported")
            if audio_status == "listened" and not nonempty(review.get("audio_notes")):
                errors.append(f"{review_label}.audio_notes is required when listened")

    if len(ids) < minimum:
        errors.append(f"unique reviewed videos: {len(ids)}; minimum required: {minimum}")
    if not channel_id and len(channels) > 1:
        errors.append(f"multiple channel_id values found: {sorted(channels)}")
    if full_watch_count < len(videos):
        warnings.append("not every video is marked full_watch; do not claim complete viewing")
    if audio_reviewed_count < len(videos):
        warnings.append("not every video is marked audio_reviewed; do not claim complete listening")

    return {
        "ok": not errors,
        "videos": len(videos),
        "unique_videos": len(ids),
        "channels": sorted(channels),
        "temporal_reviews": temporal_count,
        "full_watch": full_watch_count,
        "audio_reviewed": audio_reviewed_count,
        "errors": errors,
        "warnings": warnings,
        "scope_note": "A passing structure check does not prove that the videos were watched or interpreted correctly.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--minimum", type=int, default=10)
    parser.add_argument("--channel-id")
    parser.add_argument("--require-temporal", action="store_true")
    parser.add_argument("--require-full-watch", action="store_true")
    parser.add_argument("--require-audio", action="store_true")
    args = parser.parse_args()
    try:
        videos = load_videos(args.path)
        result = validate(
            videos,
            args.minimum,
            args.channel_id,
            args.require_temporal,
            args.require_full_watch,
            args.require_audio,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
