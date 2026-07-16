"""StoryVerifier — the continuity law. Physics gates; this only reads.

Two layers of state ride on top of the live quantum text:

- **Ink**: a strand is inked when its |z| crosses INK_THRESHOLD at a
  post-action check; the ink keeps the last confident sign while the live
  state shimmers on (in fog, the transverse drive rotates a collapse away
  within a few turns — but what the reader has read stays read). Un-inked
  strands default to the canonical bit: the transmission claims canon until
  collapsed otherwise.
- **The beat cursor**: required beats, flattened to ordered waypoints. The
  cursor advances when a stage's effective (inked) mask matches the next
  waypoint.

Discontinuity — an effective mask entering a forbidden state, moving with no
legal path through the stage's allowed masks, or stranding a remaining beat
waypoint — corrupts the run. The verifier never mutates physics and never
enters the physics hash.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from septacrypt_core.geometry.paths import find_q3_paths

from .spec import StorySpec

INK_THRESHOLD = 0.25
ROLE_BITS = (0b100, 0b010, 0b001)


@dataclass
class Verdict:
    coherent: bool
    reason: str = ""
    rule: str = ""
    stage: Optional[str] = None
    completed_beats: Tuple[str, ...] = ()


class StoryVerifier:
    def __init__(self, story: StorySpec):
        self.story = story
        self.stages = {s.name: s for s in story.stages}
        self._legal: Dict[str, List[int]] = {
            s.name: sorted(set(s.allowed_masks) - set(s.forbidden_masks))
            for s in story.stages
        }
        # (beat_id, stage, mask), beats in authored order, waypoints in order
        self.waypoints: List[Tuple[str, str, int]] = [
            (b.beat_id, stage, mask)
            for b in story.beats if b.required
            for stage, mask in b.waypoints
        ]
        self.cursor = 0
        self.ink: Dict[str, Dict[int, int]] = {s.name: {} for s in story.stages}  # bit -> ±1
        self._last_effective: Dict[str, int] = {
            s.name: s.canonical_mask for s in story.stages
        }

    # -- state reads --------------------------------------------------------
    def effective_mask(self, stage_name: str) -> int:
        s = self.stages[stage_name]
        mask = 0
        for bit in ROLE_BITS:
            inked = self.ink[stage_name].get(bit)
            up = (s.canonical_mask & bit) if inked is None else (inked > 0)
            if up:
                mask |= bit
        return mask

    def inked_strands(self, stage_name: str) -> Dict[str, int]:
        """strand name -> +1 | -1 | 0 (0 = not yet written)."""
        s = self.stages[stage_name]
        return {
            strand.name: self.ink[stage_name].get(bit, 0)
            for strand, bit in zip(s.strands, ROLE_BITS)
        }

    def next_waypoint(self) -> Optional[Tuple[str, str, int]]:
        if self.cursor < len(self.waypoints):
            return self.waypoints[self.cursor]
        return None

    def beats_complete(self) -> bool:
        return self.cursor >= len(self.waypoints)

    def legal_next_masks(self, stage_name: str) -> List[int]:
        """One Q3 step from the effective mask, within the legal set."""
        current = self.effective_mask(stage_name)
        legal = self._legal[stage_name]
        return [m for m in legal if bin(m ^ current).count("1") == 1]

    # -- the law -------------------------------------------------------------
    def check(self, game, touched: Optional[Tuple[str, str]] = None) -> Verdict:
        """Run after every committed action.

        Ink is reader-collapse only: it changes solely for the strand a read
        touched (`touched = (stage, strand)`); passive drift, bridges, and
        waits move the live state but never write text. Corruption therefore
        only ever flows from the reader's own acts."""
        if touched is not None:
            self._absorb_ink(game, touched)

        completed: List[str] = []
        for s in self.story.stages:
            prev = self._last_effective[s.name]
            new = self.effective_mask(s.name)
            if new == prev:
                continue
            if new in s.forbidden_masks:
                return self._corrupt(
                    f"the {s.name} telling entered a forbidden state "
                    f"{new:03b} — Mal_Gnosis detected",
                    rule="forbidden-mask", stage=s.name,
                )
            if not find_q3_paths(prev, new, max_steps=4, allowed_states=self._legal[s.name]):
                return self._corrupt(
                    f"no legal path {prev:03b}->{new:03b} through the "
                    f"{s.name} telling — the thread of the story is cut",
                    rule="illegal-transition", stage=s.name,
                )
            self._last_effective[s.name] = new

        # advance the beat cursor as far as the current tellings satisfy it.
        # A waypoint demands WRITTEN text: every strand inked AND the inked
        # mask matching — presumed canon doesn't count until it's been read.
        while self.cursor < len(self.waypoints):
            beat_id, stage, mask = self.waypoints[self.cursor]
            fully_inked = len(self.ink[stage]) == len(ROLE_BITS)
            if not (fully_inked and self.effective_mask(stage) == mask):
                break
            self.cursor += 1
            completed.append(beat_id)

        strand = self._stranded_waypoint()
        if strand is not None:
            beat_id, stage, mask, start = strand
            return self._corrupt(
                f"beat {beat_id!r} waypoint ({stage}, {mask:03b}) is no longer "
                f"reachable from {start:03b} — the story can no longer hit its beats",
                rule="beat-unreachable", stage=stage,
            )
        return Verdict(coherent=True, completed_beats=tuple(completed))

    def absorb_boot_ink(self, game) -> None:
        """One-time at construction: the already-written text has, by
        existing, been read — written chapters ink at their boot poles
        (and bridge-pumped fog strands ink their causal hints)."""
        for s in self.story.stages:
            for strand in s.strands:
                self._absorb_ink(game, (s.name, strand.name))

    def _absorb_ink(self, game, touched: Tuple[str, str]) -> None:
        stage_name, strand_name = touched
        s = self.stages[stage_name]
        cluster = game.world.zones[stage_name]
        for strand, bit in zip(s.strands, ROLE_BITS):
            if strand.name != strand_name:
                continue
            z = float(cluster.role_bloch(strand.name)[2])
            if abs(z) >= INK_THRESHOLD:
                self.ink[stage_name][bit] = 1 if z > 0 else -1

    def _stranded_waypoint(self) -> Optional[Tuple[str, str, int, int]]:
        cursor_mask: Dict[str, int] = {}
        for beat_id, stage, mask in self.waypoints[self.cursor:]:
            start = cursor_mask.get(stage, self.effective_mask(stage))
            if not find_q3_paths(start, mask, max_steps=4, allowed_states=self._legal[stage]):
                return (beat_id, stage, mask, start)
            cursor_mask[stage] = mask
        return None

    def _corrupt(self, reason: str, *, rule: str, stage: str) -> Verdict:
        return Verdict(coherent=False, reason=reason, rule=rule, stage=stage)
