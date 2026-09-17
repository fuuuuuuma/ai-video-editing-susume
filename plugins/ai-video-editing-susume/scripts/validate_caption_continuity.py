#!/usr/bin/env python3
"""Find logical caption gaps inside declared continuous regions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def interval(item: dict[str, Any], label: str, errors: list[str]) -> tuple[int, int] | None:
    start, end = item.get("start_frame"), item.get("end_frame")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        errors.append(f"{label} must have integer 0 <= start_frame < end_frame")
        return None
    return start, end


def subtract(base: tuple[int, int], removals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    parts = [base]
    for removal_start, removal_end in removals:
        next_parts: list[tuple[int, int]] = []
        for part_start, part_end in parts:
            if removal_end <= part_start or removal_start >= part_end:
                next_parts.append((part_start, part_end))
            else:
                if part_start < removal_start:
                    next_parts.append((part_start, removal_start))
                if removal_end < part_end:
                    next_parts.append((removal_end, part_end))
        parts = next_parts
    return parts


def merge(intervals: list[tuple[int, int]]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    merged: list[tuple[int, int]] = []
    overlaps: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        if start < previous_end:
            overlaps.append((start, min(previous_end, end)))
        merged[-1] = (previous_start, max(previous_end, end))
    return merged, overlaps


def gaps(segment: tuple[int, int], coverage: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = segment[0]
    for start, end in coverage:
        if end <= segment[0] or start >= segment[1]:
            continue
        clipped_start, clipped_end = max(start, segment[0]), min(end, segment[1])
        if clipped_start > cursor:
            result.append((cursor, clipped_start))
        cursor = max(cursor, clipped_end)
    if cursor < segment[1]:
        result.append((cursor, segment[1]))
    return result


def validate(payload: dict[str, Any], forbid_overlap: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    continuous = payload.get("continuous_regions")
    captions = payload.get("captions")
    excluded = payload.get("excluded_regions", [])
    if not isinstance(continuous, list) or not continuous:
        errors.append("continuous_regions must be a non-empty array")
        continuous = []
    if not isinstance(captions, list) or not captions:
        errors.append("captions must be a non-empty array")
        captions = []
    if not isinstance(excluded, list):
        errors.append("excluded_regions must be an array")
        excluded = []

    continuous_intervals = [value for index, item in enumerate(continuous) if isinstance(item, dict) and (value := interval(item, f"continuous_regions[{index}]", errors))]
    excluded_intervals: list[tuple[int, int]] = []
    for index, item in enumerate(excluded):
        if not isinstance(item, dict):
            errors.append(f"excluded_regions[{index}] must be an object")
            continue
        value = interval(item, f"excluded_regions[{index}]", errors)
        if value:
            excluded_intervals.append(value)
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            errors.append(f"excluded_regions[{index}].reason is required")

    caption_intervals: list[tuple[int, int]] = []
    ids: set[str] = set()
    for index, caption in enumerate(captions):
        label = f"captions[{index}]"
        if not isinstance(caption, dict):
            errors.append(f"{label} must be an object")
            continue
        caption_id = caption.get("id")
        if not isinstance(caption_id, str) or not caption_id.strip():
            errors.append(f"{label}.id is required")
        elif caption_id in ids:
            errors.append(f"duplicate caption id: {caption_id}")
        else:
            ids.add(caption_id)
        value = interval(caption, label, errors)
        if value:
            caption_intervals.append(value)
        if caption.get("visible") is False or caption.get("opacity", 1) <= 0 or caption.get("scale", 1) <= 0:
            errors.append(f"{label} is logically present but not visible")
        if not str(caption.get("text", "")).strip() and not str(caption.get("asset", "")).strip():
            errors.append(f"{label} needs text or an asset")

    coverage, overlap_ranges = merge(caption_intervals)
    all_gaps: list[tuple[int, int]] = []
    for region in continuous_intervals:
        for segment in subtract(region, excluded_intervals):
            all_gaps.extend(gaps(segment, coverage))
    if all_gaps:
        errors.append(f"caption gaps found: {all_gaps}")
    if overlap_ranges:
        message = f"caption overlaps found: {overlap_ranges}; confirm simultaneous speech or replacement logic"
        (errors if forbid_overlap else warnings).append(message)

    return {
        "ok": not errors,
        "caption_count": len(caption_intervals),
        "gaps": all_gaps,
        "overlaps": overlap_ranges,
        "errors": errors,
        "warnings": warnings,
        "scope_note": "Logical coverage does not prove sync, readability, contrast, or final pixels.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--forbid-overlap", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("root must be an object")
        result = validate(payload, args.forbid_overlap)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "errors": [str(exc)], "warnings": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
