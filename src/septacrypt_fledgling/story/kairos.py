"""Kairos — the transmission's own process clock, read from Berry phase.

Two honest jobs, both read-only over physics (geometric nearness never
mints a causal edge, and never gates anything):

- chapter_phase: accumulated geometric phase per stage-zone — how much
  *process* a chapter has lived through, as distinct from wall ticks.
- loop detection: if a stage's Bloch endpoint returns close to an earlier
  snapshot while the beat cursor hasn't advanced, the reader is walking a
  circle — surfaced as a flag (and a Seer hint), nothing more.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

_TRAIL_CAP = 64
_RETURN_EPS = 0.08
_MIN_SEPARATION = 3   # checks apart before a return counts as a loop
_EXCURSION_MIN = 0.2  # the path must actually have gone somewhere — a static
                      # written chapter is settled, not looping


class KairosTracker:
    def __init__(self) -> None:
        # stage -> list of (z_tuple, cursor) snapshots, one per committed action
        self._trail: Dict[str, List[Tuple[Tuple[float, ...], int]]] = {}

    def observe(self, session: Any) -> None:
        for s in session.story.stages:
            cluster = session.world.zones[s.name]
            snap = tuple(
                round(float(cluster.role_bloch(st.name)[2]), 4) for st in s.strands
            )
            trail = self._trail.setdefault(s.name, [])
            trail.append((snap, session.verifier.cursor))
            if len(trail) > _TRAIL_CAP:
                del trail[0]

    def looping(self, stage_name: str) -> bool:
        trail = self._trail.get(stage_name, [])
        if len(trail) < _MIN_SEPARATION + 1:
            return False
        current, cursor = trail[-1]
        for i, (past, past_cursor) in enumerate(trail[: -_MIN_SEPARATION]):
            if past_cursor != cursor:
                continue  # the story moved on since — not a loop
            if max(abs(a - b) for a, b in zip(current, past)) >= _RETURN_EPS:
                continue  # not a return
            excursion = max(
                max(abs(a - b) for a, b in zip(snap, current))
                for snap, _ in trail[i:]
            )
            if excursion >= _EXCURSION_MIN:
                return True  # went somewhere, came back, story didn't advance
        return False


def chapter_phase(session: Any, stage_name: str) -> Dict[str, Any]:
    journey = session.world.berry.get(stage_name)
    if journey is None:
        return {"total_phase": 0.0, "per_role": {}}
    coord = journey.coordinate(session.world.zones[stage_name])
    return {
        "total_phase": coord.get("total_phase", 0.0),
        "per_role": coord.get("per_role", {}),
    }
