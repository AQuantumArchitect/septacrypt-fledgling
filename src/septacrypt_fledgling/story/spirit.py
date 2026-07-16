"""Spirit — meaning ranks the legal continuations; physics gates them.

Each voice carries a 7-axis frame (StorySpec.voices); each (stage, mask)
carries a value vector (StorySpec.state_values). The ranking reorders the
verifier's legal-next-mask set per voice and can NEVER add a mask to it —
"spirit reorders, never legalizes" is gated in tests.
"""
from __future__ import annotations

from typing import Dict, List

from septacrypt_core.spirit.vector import SpiritVector

from .spec import SPIRIT_AXES, StorySpec


def _vector(values, frame_id: str) -> SpiritVector:
    return SpiritVector(**dict(zip(SPIRIT_AXES, values)), frame_id=frame_id, confidence=1.0)


class SpiritFrames:
    def __init__(self, story: StorySpec):
        self.frames: Dict[str, SpiritVector] = {
            v.name: _vector(v.spirit_frame, f"voice:{v.name}") for v in story.voices
        }
        self.state_values: Dict[str, Dict[int, SpiritVector]] = {}
        for stage_name, mask, vec in story.state_values:
            self.state_values.setdefault(stage_name, {})[mask] = _vector(
                vec, f"state:{stage_name}:{mask:03b}"
            )

    def rank(self, stage_name: str, legal_masks: List[int]) -> Dict[str, List[int]]:
        """voice -> the SAME legal masks, reordered by that voice's frame."""
        values = self.state_values.get(stage_name, {})
        out: Dict[str, List[int]] = {}
        for voice, frame in self.frames.items():
            def score(mask: int) -> float:
                sv = values.get(mask)
                return sv.dot(frame) if sv is not None else 0.0

            out[voice] = sorted(legal_masks, key=lambda m: (-score(m), m))
        return out
