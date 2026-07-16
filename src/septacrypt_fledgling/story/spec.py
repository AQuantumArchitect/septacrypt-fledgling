"""StorySpec — a partially written book as data.

Deliberate sibling of septacrypt-core's WorldSpec and umwelt's DomainSpec,
mirroring their ergonomics (frozen dataclasses, validate() -> List[str])
without extending either. A StorySpec declares narrative structure — stages,
strands, beats, voices, causal links — and compiles down to a WorldSpec
(compile.py). It never touches physics itself.

Mask semantics: bit b of a stage's mask means "strand b stands realized in
this telling" (z→+1 canon-as-written, z→-1 lost/retold, z≈0 not yet
written). forbidden_masks are Guard-redacted states — entering one is
instant corruption of the transmission (the loss condition, diegetic).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from septacrypt_core.geometry.paths import find_q3_paths

SPIRIT_AXES = ("wisdom", "might", "wealth", "power", "glory", "honor", "blessing")


@dataclass(frozen=True)
class StrandSpec:
    """One qubit-role of a stage; the glosses give the poles narrative meaning."""

    name: str
    gloss_up: str    # what z -> +1 means (canon as written)
    gloss_down: str  # what z -> -1 means (lost / dormant / retold)


@dataclass(frozen=True)
class PassageSpec:
    """One data-layer span of the manuscript, attributed to a voice."""

    passage_id: str
    stage: str
    voice: str            # foreword|guard|translator|seer|myth|outline|appendix|chrome
    order: int
    text: str
    rs_removal: int = 0       # R# — degrees of removal from first-hand knowledge
    rs_speculation: int = 0   # S# — degrees of speculation
    corrupted: bool = False   # Guard [bracketed] patch present
    stub: bool = False        # [[structural synopsis]] — unwritten section
    anchor_masks: Tuple[int, ...] = ()  # masks this passage attests (authored)


@dataclass(frozen=True)
class StageSpec:
    """One chapter-zone: three strands, a canonical telling, legal masks, fog."""

    name: str
    order: int
    era: str
    strands: Tuple[StrandSpec, ...]
    canonical_mask: int
    allowed_masks: Tuple[int, ...]
    forbidden_masks: Tuple[int, ...] = ()
    fog: float = 0.0  # 0.0 fully written .. 1.0 deep superposition
    passages: Tuple[PassageSpec, ...] = ()

    @property
    def strand_names(self) -> Tuple[str, ...]:
        return tuple(s.name for s in self.strands)


@dataclass(frozen=True)
class BeatSpec:
    """An ordered sequence of (stage, mask) waypoints the run must visit."""

    beat_id: str
    description: str
    waypoints: Tuple[Tuple[str, int], ...]
    required: bool = True


@dataclass(frozen=True)
class CausalLinkSpec:
    """Book causality: collapsing src biases dst — compiles to a BridgeSpec."""

    src_stage: str
    src_strand: str
    dst_stage: str
    dst_strand: str
    alpha: float


@dataclass(frozen=True)
class VoiceSpec:
    """A manuscript voice as an observer mind + a spirit frame."""

    name: str
    register: str  # prompt fragment for the narrator (contain/gloss/revere/witness/bless)
    observes: Tuple[Tuple[str, str], ...]  # (stage, strand) channels this voice senses
    efficiency: float = 0.9                # measurement efficiency of this witness
    spirit_frame: Tuple[float, ...] = (0.0,) * 7  # weights over SPIRIT_AXES


@dataclass(frozen=True)
class StorySpec:
    story_id: str
    version: str
    stages: Tuple[StageSpec, ...]
    beats: Tuple[BeatSpec, ...]
    voices: Tuple[VoiceSpec, ...] = ()
    links: Tuple[CausalLinkSpec, ...] = ()
    # (stage, mask, 7-tuple over SPIRIT_AXES) — meaning of each state
    state_values: Tuple[Tuple[str, int, Tuple[float, ...]], ...] = ()
    attention: Optional[float] = None

    def stage(self, name: str) -> StageSpec:
        for s in self.stages:
            if s.name == name:
                return s
        raise KeyError(f"unknown stage {name!r}")

    def stages_by_name(self) -> Dict[str, StageSpec]:
        return {s.name: s for s in self.stages}

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.story_id:
            errors.append("story_id must be non-empty")
        if not self.stages:
            errors.append("at least one stage required")

        names = [s.name for s in self.stages]
        if len(set(names)) != len(names):
            errors.append("duplicate stage names")
        by_name = {s.name: s for s in self.stages}
        orders = [s.order for s in self.stages]
        if sorted(orders) != list(range(len(orders))):
            errors.append("stage orders must be a permutation of 0..n-1")

        for s in self.stages:
            n = len(s.strands)
            if n != 3:
                errors.append(
                    f"stage {s.name!r}: {n} strands — v1 requires exactly 3 "
                    "(compiles to Q3 zones)"
                )
            snames = [x.name for x in s.strands]
            if len(set(snames)) != len(snames):
                errors.append(f"stage {s.name!r}: duplicate strand names")
            limit = 2 ** n
            for label, masks in (("allowed", s.allowed_masks), ("forbidden", s.forbidden_masks)):
                for m in masks:
                    if not (0 <= m < limit):
                        errors.append(f"stage {s.name!r}: {label} mask {m} out of range")
            if not s.allowed_masks:
                errors.append(f"stage {s.name!r}: allowed_masks must be non-empty")
            if s.canonical_mask not in s.allowed_masks:
                errors.append(f"stage {s.name!r}: canonical_mask not in allowed_masks")
            overlap = set(s.allowed_masks) & set(s.forbidden_masks)
            if overlap:
                errors.append(f"stage {s.name!r}: masks {sorted(overlap)} both allowed and forbidden")
            if not (0.0 <= s.fog <= 1.0):
                errors.append(f"stage {s.name!r}: fog {s.fog} outside [0, 1]")
            for p in s.passages:
                if p.stage != s.name:
                    errors.append(f"stage {s.name!r}: passage {p.passage_id} claims stage {p.stage!r}")

        beat_ids = [b.beat_id for b in self.beats]
        if len(set(beat_ids)) != len(beat_ids):
            errors.append("duplicate beat ids")
        for b in self.beats:
            if not b.waypoints:
                errors.append(f"beat {b.beat_id!r}: no waypoints")
            last_order = -1
            for stage_name, mask in b.waypoints:
                s = by_name.get(stage_name)
                if s is None:
                    errors.append(f"beat {b.beat_id!r}: unknown stage {stage_name!r}")
                    continue
                if mask not in s.allowed_masks:
                    errors.append(
                        f"beat {b.beat_id!r}: waypoint mask {mask:03b} not allowed in {stage_name!r}"
                    )
                if s.order < last_order:
                    errors.append(f"beat {b.beat_id!r}: waypoints out of chronological order")
                last_order = s.order

        errors.extend(self._beat_closure_errors(by_name))

        for l in self.links:
            for stage_name, strand in ((l.src_stage, l.src_strand), (l.dst_stage, l.dst_strand)):
                s = by_name.get(stage_name)
                if s is None:
                    errors.append(f"link references unknown stage {stage_name!r}")
                elif strand not in s.strand_names:
                    errors.append(f"link references unknown strand {stage_name}.{strand}")
            if not (0.0 < l.alpha <= 1.0):
                errors.append(f"link alpha {l.alpha} outside (0, 1]")

        seen_voices = set()
        for v in self.voices:
            if v.name in seen_voices:
                errors.append(f"duplicate voice {v.name!r}")
            seen_voices.add(v.name)
            if len(v.spirit_frame) != len(SPIRIT_AXES):
                errors.append(f"voice {v.name!r}: spirit_frame must have {len(SPIRIT_AXES)} axes")
            for stage_name, strand in v.observes:
                s = by_name.get(stage_name)
                if s is None:
                    errors.append(f"voice {v.name!r} observes unknown stage {stage_name!r}")
                elif strand not in s.strand_names:
                    errors.append(f"voice {v.name!r} observes unknown strand {stage_name}.{strand}")
            if not (0.0 < v.efficiency <= 1.0):
                errors.append(f"voice {v.name!r}: efficiency outside (0, 1]")

        for stage_name, mask, vec in self.state_values:
            s = by_name.get(stage_name)
            if s is None:
                errors.append(f"state_values references unknown stage {stage_name!r}")
            elif not (0 <= mask < 2 ** len(s.strands)):
                errors.append(f"state_values mask {mask} out of range for {stage_name!r}")
            if len(vec) != len(SPIRIT_AXES):
                errors.append(f"state_values for ({stage_name}, {mask}): need {len(SPIRIT_AXES)} axes")

        if self.attention is not None and self.attention <= 0:
            errors.append("attention must be positive or None")
        return errors

    def _beat_closure_errors(self, by_name: Dict[str, StageSpec]) -> List[str]:
        """Narrative resource closure (the Universal-Architect idea reborn):
        every required beat waypoint must be symbolically reachable within its
        stage's allowed masks — from the canonical start, then waypoint to
        waypoint. A story whose beats can't close doesn't compile."""
        errors: List[str] = []
        cursor: Dict[str, int] = {}  # stage -> last waypoint mask reached
        for b in self.beats:
            if not b.required:
                continue
            for stage_name, mask in b.waypoints:
                s = by_name.get(stage_name)
                if s is None or mask not in s.allowed_masks:
                    continue  # already reported above
                start = cursor.get(stage_name, s.canonical_mask)
                allowed = list(set(s.allowed_masks) - set(s.forbidden_masks))
                if not find_q3_paths(start, mask, max_steps=4, allowed_states=allowed):
                    errors.append(
                        f"beat {b.beat_id!r}: waypoint ({stage_name}, {mask:03b}) "
                        f"unreachable from {start:03b} within allowed masks — "
                        "narrative closure fails"
                    )
                cursor[stage_name] = mask
        return errors
