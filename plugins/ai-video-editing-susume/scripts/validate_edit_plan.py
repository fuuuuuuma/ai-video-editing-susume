#!/usr/bin/env python3
"""Validate that an edit plan connects every required editorial area to output events."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CHANNELS = {"ai-video-editing-susume", "ai-monetize", "ccaa", "instagram-okuyama", "other-youtube"}
AREAS = ("initial_layout", "cuts", "captions", "framing", "images", "se", "bgm", "cta", "qa")
STATUSES = {"use", "omit", "not_applicable"}
INSTAGRAM_FORMATS = {"tier", "ranking", "quadrant", "comparison-grid", "explainer", "story", "mixed"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_event(event: Any, label: str, errors: list[str]) -> None:
    if not isinstance(event, dict):
        errors.append(f"{label} must be an object")
        return
    for field in ("id", "cue", "reference"):
        if not nonempty(event.get(field)):
            errors.append(f"{label}.{field} is required")
    start, end = event.get("start_frame"), event.get("end_frame")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        errors.append(f"{label} must have integer 0 <= start_frame < end_frame")
    members = event.get("members")
    if not isinstance(members, list) or not members:
        errors.append(f"{label}.members must contain implementation ids")
    elif any(not nonempty(member) for member in members):
        errors.append(f"{label}.members must contain non-empty strings")


def validate_speakers(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    speaker_data = payload.get("speaker_captions")
    if not isinstance(speaker_data, dict):
        errors.append("speaker_captions is required for ai-monetize")
        return
    if not nonempty(speaker_data.get("evidence_policy")):
        errors.append("speaker_captions.evidence_policy is required")
    utterances = speaker_data.get("utterances")
    if not isinstance(utterances, list) or not utterances:
        errors.append("speaker_captions.utterances must be a non-empty array")
        return
    speakers: set[str] = set()
    styles: dict[str, set[str]] = {}
    ids: set[str] = set()
    for index, utterance in enumerate(utterances):
        label = f"speaker_captions.utterances[{index}]"
        if not isinstance(utterance, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("utterance_id", "speaker_id", "style_id", "rendered_layer_id", "evidence"):
            if not nonempty(utterance.get(field)):
                errors.append(f"{label}.{field} is required")
        utterance_id = utterance.get("utterance_id")
        if nonempty(utterance_id) and utterance_id in ids:
            errors.append(f"duplicate utterance_id: {utterance_id}")
        ids.add(utterance_id)
        speaker = utterance.get("speaker_id")
        style = utterance.get("style_id")
        if nonempty(speaker) and nonempty(style):
            speakers.add(speaker)
            styles.setdefault(speaker, set()).add(style)
    if len(speakers) > 1:
        flattened = {style for style_set in styles.values() for style in style_set}
        if len(flattened) < 2:
            errors.append("multiple speakers cannot all collapse to one caption style")
    elif len(speakers) == 1:
        warnings.append("only one speaker is present; confirm this matches the actual audio")


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    channel = payload.get("channel")
    if channel not in CHANNELS:
        errors.append(f"channel must be one of {sorted(CHANNELS)}")
    if not nonempty(payload.get("primary_reference")):
        errors.append("primary_reference is required")
    if not nonempty(payload.get("format")):
        errors.append("format is required")

    areas = payload.get("areas")
    if not isinstance(areas, dict):
        errors.append("areas must be an object")
        areas = {}
    event_ids: set[str] = set()
    for area_name in AREAS:
        area = areas.get(area_name)
        label = f"areas.{area_name}"
        if not isinstance(area, dict):
            errors.append(f"{label} is required")
            continue
        status = area.get("status")
        if status not in STATUSES:
            errors.append(f"{label}.status must be use, omit, or not_applicable")
            continue
        if not nonempty(area.get("reason")):
            errors.append(f"{label}.reason is required")
        if status == "use":
            if not nonempty(area.get("reference")):
                errors.append(f"{label}.reference is required when used")
            events = area.get("events")
            if not isinstance(events, list) or not events:
                errors.append(f"{label}.events must be non-empty when used")
                continue
            for event_index, event in enumerate(events):
                validate_event(event, f"{label}.events[{event_index}]", errors)
                if isinstance(event, dict) and nonempty(event.get("id")):
                    event_id = event["id"]
                    if event_id in event_ids:
                        errors.append(f"duplicate event id: {event_id}")
                    event_ids.add(event_id)
        elif area.get("events"):
            errors.append(f"{label}.events must be empty when status is {status}")

    semantic_review = payload.get("semantic_review")
    if not isinstance(semantic_review, list) or not semantic_review:
        errors.append("semantic_review must cover the full content with at least one decision")
    else:
        for index, decision in enumerate(semantic_review):
            label = f"semantic_review[{index}]"
            if not isinstance(decision, dict):
                errors.append(f"{label} must be an object")
                continue
            for field in ("id", "source_range", "output_range", "decision", "reason"):
                if not nonempty(decision.get(field)):
                    errors.append(f"{label}.{field} is required")

    if channel == "ai-monetize":
        validate_speakers(payload, errors, warnings)
    if channel == "instagram-okuyama" and payload.get("format") not in INSTAGRAM_FORMATS:
        errors.append(f"Instagram format must be one of {sorted(INSTAGRAM_FORMATS)}")
    if channel == "other-youtube" and not nonempty(payload.get("channel_study_file")):
        errors.append("channel_study_file is required for other-youtube")

    return {
        "ok": not errors,
        "channel": channel,
        "implemented_event_ids": sorted(event_ids),
        "errors": errors,
        "warnings": warnings,
        "scope_note": "This validates plan-to-implementation links, not editorial quality or media playback.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("root must be an object")
        result = validate(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
