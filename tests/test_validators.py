from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "ai-video-editing-susume" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_caption_continuity  # noqa: E402
import validate_channel_study  # noqa: E402
import validate_edit_plan  # noqa: E402


def study_video(index: int) -> dict:
    return {
        "id": f"video-{index}",
        "channel_id": "channel-1",
        "title": f"Video {index}",
        "url": f"https://www.youtube.com/watch?v=video-{index}",
        "date": "20260901",
        "duration": 120.0,
        "visual_reviewed": True,
        "full_watch": False,
        "audio_reviewed": False,
        "temporal_reviews": [
            {
                "start": float(offset),
                "end": float(offset + 2),
                "method": "video_playback",
                "evidence_ref": f"review-{index}-{offset}",
                "before": "normal",
                "entry": "element enters",
                "hold": "element stays",
                "exit": "returns to normal",
                "caption_interaction": "replaces the normal caption",
                "audio_status": "listened",
                "audio_notes": "heard the voice and effect",
            }
            for offset in (1, 10, 20)
        ],
    }


def event(area: str, index: int) -> dict:
    return {
        "id": f"{area}-{index}",
        "cue": f"cue for {area}",
        "reference": f"reference for {area}",
        "start_frame": index * 30,
        "end_frame": (index + 1) * 30,
        "members": [f"layer-{area}-{index}"],
    }


def edit_plan(channel: str = "ccaa") -> dict:
    areas = {}
    for index, area in enumerate(validate_edit_plan.AREAS):
        areas[area] = {
            "status": "use",
            "reason": f"needed for {area}",
            "reference": f"reference for {area}",
            "events": [event(area, index)],
        }
    return {
        "channel": channel,
        "primary_reference": "video-id 00:00-01:00",
        "format": "explainer",
        "areas": areas,
        "semantic_review": [
            {
                "id": "segment-1",
                "source_range": "0.0-4.0",
                "output_range": "0-120f",
                "decision": "keep",
                "reason": "complete opening statement",
            }
        ],
    }


class ChannelStudyTests(unittest.TestCase):
    def test_ten_distinct_temporal_reviews_pass(self) -> None:
        result = validate_channel_study.validate(
            [study_video(index) for index in range(10)],
            minimum=10,
            channel_id="channel-1",
            require_temporal=True,
            require_full_watch=False,
            require_audio=False,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["temporal_reviews"], 30)
        self.assertTrue(result["warnings"])

    def test_duplicate_video_does_not_satisfy_minimum(self) -> None:
        videos = [study_video(index) for index in range(9)] + [study_video(0)]
        result = validate_channel_study.validate(videos, 10, "channel-1", True, False, False)
        self.assertFalse(result["ok"])
        self.assertTrue(any("duplicates" in error for error in result["errors"]))


class EditPlanTests(unittest.TestCase):
    def test_connected_plan_passes(self) -> None:
        result = validate_edit_plan.validate(edit_plan())
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["implemented_event_ids"]), len(validate_edit_plan.AREAS))

    def test_ai_monetize_requires_distinct_speaker_styles(self) -> None:
        plan = edit_plan("ai-monetize")
        plan["speaker_captions"] = {
            "evidence_policy": "confirmed from isolated microphones",
            "utterances": [
                {"utterance_id": "u1", "speaker_id": "a", "style_id": "same", "rendered_layer_id": "l1", "evidence": "mic A"},
                {"utterance_id": "u2", "speaker_id": "b", "style_id": "same", "rendered_layer_id": "l2", "evidence": "mic B"},
            ],
        }
        result = validate_edit_plan.validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("one caption style" in error for error in result["errors"]))


class CaptionTests(unittest.TestCase):
    def test_adjacent_captions_cover_region(self) -> None:
        payload = {
            "continuous_regions": [{"start_frame": 0, "end_frame": 90}],
            "excluded_regions": [],
            "captions": [
                {"id": "c1", "start_frame": 0, "end_frame": 30, "text": "one"},
                {"id": "c2", "start_frame": 30, "end_frame": 90, "text": "two"},
            ],
        }
        self.assertTrue(validate_caption_continuity.validate(payload, False)["ok"])

    def test_gap_fails(self) -> None:
        payload = {
            "continuous_regions": [{"start_frame": 0, "end_frame": 90}],
            "excluded_regions": [],
            "captions": [
                {"id": "c1", "start_frame": 0, "end_frame": 30, "text": "one"},
                {"id": "c2", "start_frame": 31, "end_frame": 90, "text": "two"},
            ],
        }
        result = validate_caption_continuity.validate(payload, False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["gaps"], [(30, 31)])


if __name__ == "__main__":
    unittest.main()
