"""Nested Reactor retro-solver: 'the reactor is hot — what happened?'

Layers, in the kernel's own law (physics constrains; spirit ranks legal
options; narrative expresses):

1. generate_candidates — symbolic Q3 paths between the checkpoint mask and
   the observed mask (septacrypt_core RetroSolver / TransitionVerifier), each
   labeled by the roles whose bits flip, plus the honest 'unknown' candidate.
2. rank_by_belief — an observer's private beliefs re-rank candidates: a
   candidate whose hypothesized flips agree with what the observer has
   actually seen scores higher. Probing (LOOK) changes this ranking; that IS
   the investigation loop.
3. propose_insertion — Microscope-style: a proposed history insertion is
   accepted (fork minted on a new ledger branch) only if every step is
   Q3-adjacent; rejections name the violated constraint.
4. spirit_rank — SpiritScorer orders the VALID candidates under a value
   frame. It receives only verifier-approved paths, so it can reorder but
   never legalize.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from septacrypt_core.dynamics.transition import TransitionVerifier
from septacrypt_core.ledger.replay import RetroSolver
from septacrypt_core.spirit.vector import SpiritScorer, SpiritVector

Q3_ALL = list(range(8))
# Bit convention matches geometry/atlas.py axis order: role[0] is the high bit.
ROLE_BITS = (0b100, 0b010, 0b001)


@dataclass
class Candidate:
    label: str
    path: Tuple[int, ...]  # masks from checkpoint to observed, inclusive
    flipped_roles: Tuple[str, ...]
    score: float = 0.0
    notes: str = ""


@dataclass
class InsertionVerdict:
    accepted: bool
    reason: str
    branch_id: Optional[str] = None
    fork_head: Optional[str] = None


def _flipped_roles(path: Sequence[int], roles: Sequence[str]) -> Tuple[str, ...]:
    flipped = []
    for a, b in zip(path, path[1:]):
        xor = a ^ b
        for role, bit in zip(roles, ROLE_BITS):
            if xor & bit:
                flipped.append(role)
    return tuple(dict.fromkeys(flipped))  # ordered, deduped


def generate_candidates(
    checkpoint_mask: int,
    observed_mask: int,
    roles: Sequence[str],
    *,
    max_steps: int = 3,
) -> List[Candidate]:
    solver = RetroSolver(Q3_ALL)
    paths = solver.solve_insertion(checkpoint_mask, observed_mask, max_steps=max_steps)
    candidates = [
        Candidate(
            label=" + ".join(_flipped_roles(p, roles)) or "no-change",
            path=tuple(p),
            flipped_roles=_flipped_roles(p, roles),
        )
        for p in paths
    ]
    candidates.append(
        Candidate(
            label="unknown/unmodeled cause",
            path=(),
            flipped_roles=(),
            notes="always on the table — the model may be wrong",
        )
    )
    return candidates


def rank_by_belief(
    candidates: List[Candidate],
    belief_z: Dict[str, float],
    roles: Sequence[str],
    observed_mask: int,
) -> List[Candidate]:
    """Score = end-state agreement with the observer's belief signs, minus a
    parsimony penalty per extra hypothesized event. Candidates sharing an
    endpoint tie on evidence — Occam separates them explicitly rather than
    leaving the choice to sort stability. `unknown` keeps a small floor."""
    for c in candidates:
        if not c.path:
            c.score = 0.05  # unknown: never zero, never favored while a model fits
            continue
        end = c.path[-1]
        agreement = 0.0
        for role, bit in zip(roles, ROLE_BITS):
            z = belief_z.get(role)
            if z is None:
                continue
            implied = 1.0 if (end & bit) else -1.0
            agreement += implied * z
        parsimony = 0.1 * (len(c.path) - 2)  # extra steps beyond the direct path
        c.score = round(agreement / max(len(roles), 1) - parsimony, 4)
    return sorted(candidates, key=lambda c: -c.score)


def propose_insertion(
    session,
    *,
    start_mask: int,
    proposed_path: Sequence[int],
    branch_id: str = "counterfactual",
) -> InsertionVerdict:
    """Verify a proposed inserted history symbolically; on acceptance, mint a
    fork branch in the session's ledger anchored at the current head.

    The symbolic gate is necessary but not sufficient (dynamical realizability
    is the certificate layer's job); a symbolic rejection is final."""
    if not proposed_path or proposed_path[0] != start_mask:
        return InsertionVerdict(False, "path must start at the checkpoint mask")
    for a, b in zip(proposed_path, proposed_path[1:]):
        if not TransitionVerifier.verify_step(a, b):
            return InsertionVerdict(
                False,
                f"Q3 non-adjacent step {a:03b}->{b:03b} "
                f"(Hamming distance {bin(a ^ b).count('1')} != 1) — "
                "no teleportation across state space",
            )
    if session.ledger is None:
        return InsertionVerdict(True, "symbolically valid (no ledger to fork)")
    head_id = session.ledger.branches.get("main")
    if head_id is None:
        return InsertionVerdict(False, "no committed history to fork from")
    session.ledger.branch(head_id, branch_id)
    return InsertionVerdict(
        True,
        "symbolically valid — forked for counterfactual replay",
        branch_id=branch_id,
        fork_head=head_id,
    )


def spirit_rank(
    candidates: List[Candidate],
    frame: SpiritVector,
    state_values: Dict[int, SpiritVector],
) -> List[Candidate]:
    """Order verifier-approved candidates by resonance under a value frame.
    Candidates without a path (unknown) keep their place at the bottom."""
    with_path = [c for c in candidates if c.path]
    without = [c for c in candidates if not c.path]
    ranked = sorted(
        with_path,
        key=lambda c: -SpiritScorer.score_candidate_path(list(c.path), frame, state_values),
    )
    return ranked + without
