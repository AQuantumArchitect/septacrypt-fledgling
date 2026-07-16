"""Deterministic offline narration: canonical passages where the telling
matches the written text, register-true templates elsewhere. A pure
function of (story, stage, inked strands, voice, verb) — no RNG, no clock,
no network — so replays and tests are bit-stable."""
from __future__ import annotations

from typing import Dict, Optional

from ..story.spec import StageSpec, StorySpec

_ANCHOR_LIMIT = 320  # chars of canonical passage quoted per narration


def _gloss(stage: StageSpec, strand_name: str, ink: int) -> str:
    for strand in stage.strands:
        if strand.name == strand_name:
            if ink > 0:
                return strand.gloss_up
            if ink < 0:
                return strand.gloss_down
            return f"the {strand_name} strand still shimmers unwritten"
    raise ValueError(f"unknown strand {strand_name!r} in {stage.name}")


def _canonical_quote(stage: StageSpec, voice: str) -> Optional[str]:
    for p in stage.passages:
        if p.voice == voice and not p.stub:
            text = p.text[:_ANCHOR_LIMIT]
            return text + ("…" if len(p.text) > _ANCHOR_LIMIT else "")
    return None


def narrate_offline(
    story: StorySpec,
    stage_name: str,
    inked: Dict[str, int],
    voice: str,
    verb: str,
    strand: Optional[str] = None,
) -> str:
    stage = story.stage(stage_name)
    if verb in ("wait", "stir"):
        line = {
            "guard": "[Fear not. The transmission plays on. No Guard subroutine tripped.]",
            "translator": f"(time passes in the {stage.name} telling; the Semantic Sea shifts beneath it)",
            "seer": "{The story breathes. Attend, treasure of the cosmos.}",
            "rasi": "And so time passed, as it does, whether or not anyone was telling it.",
            "paul": "Be patient with the story. Go in God's peace.",
        }[voice]
        return line

    target = strand or stage.strands[0].name
    ink = inked.get(target, 0)
    gloss = _gloss(stage, target, ink)

    # If the whole stage stands at canon, quote the written text itself.
    if voice == "rasi" and ink != 0:
        quote = _canonical_quote(stage, "myth")
        if quote and all(
            inked.get(s.name, 0) == (1 if (stage.canonical_mask & bit) else -1)
            for s, bit in zip(stage.strands, (0b100, 0b010, 0b001))
        ):
            return f"{quote}\n\nSo it stands written, as I told it: {gloss}."

    templates = {
        "guard": f"[Fear not. {stage.name} strand r3constructed: {gloss}. "
                 "Your humanity is your checksum.]",
        "translator": f"(the {stage.name} telling now reads: {gloss} — semantic "
                      "fidelity moderate, the S3mantic S34 permitting)",
        "seer": f"{{Behold, within {stage.name}: {gloss}. Rejoyce those within the shell.}}",
        "rasi": f"I read it again to be sure, and it was so: {gloss}. "
                "Perhaps that is the way it was always going to be told.",
        "paul": f"To the degree it matters to you, reader: {gloss}. Go in God's peace.",
    }
    return templates[voice]
