"""StoryCompiler — the Structure face made real.

compile_hierarchy(StorySpec) -> WorldSpec: the book's structure compiles to
authoritative ground physics. Stages become zones (strands = qubit roles);
fog becomes transverse field (real superposition drive) while written-ness
becomes longitudinal field toward the canonical poles; causal links become
bridges (collapsing early chapters biases the fog downstream); each stage's
final required waypoint becomes its quest. Beat ORDER is enforced by the
host StoryVerifier, not by core quests.

Conforms to contracts.StructureFace by test, never by inheritance.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from septacrypt_core.spec.types import BridgeSpec, QuestSpec, WorldSpec, ZoneSpec

from .spec import StorySpec

# Field scales. HZ_MAX keeps written chapters pinned near canon; HX_MAX drives
# genuine superposition in fog. Both well inside the empirically stable range
# (pure fields stable to |h|=5; STIR_H_MAX caps at 2.0).
HZ_MAX = 1.2
HX_MAX = 1.0
INIT_Z_WRITTEN = 0.9  # construction pole depth scales with written-ness
INTRA_ZZ = 0.05        # weak intra-triad coupling — strands of one telling cohere
GAMMA = 0.01           # slow amplitude damping; canon must persist between readings
DT = 0.1

# Story strands are UNITARY qubits: collapsed text persists (precession, slow
# damping) instead of thermalizing to the mixed state within a few turns as
# the name-based default ("dissipative", gamma_diss=5.0) would. This is the
# load-bearing difference between a reactor you monitor and a book you read.
ROLE_MODES = ("unitary", "unitary", "unitary")

# Bit convention matches geometry/atlas.py and retro/solver.py: role[0] = high bit.
ROLE_BITS = (0b100, 0b010, 0b001)


def _pole(mask: int, bit: int) -> float:
    return 1.0 if (mask & bit) else -1.0


class StoryCompiler:
    """StructureFace conformer: compile the book-tree into a WorldSpec."""

    def compile_hierarchy(self, root: StorySpec) -> WorldSpec:
        errors = root.validate()
        if errors:
            raise ValueError(f"invalid StorySpec {root.story_id!r}: " + "; ".join(errors))

        stages = sorted(root.stages, key=lambda s: s.order)
        zones: List[ZoneSpec] = []
        for s in stages:
            written = 1.0 - s.fog
            h_fields: List[Tuple[float, float, float]] = []
            init_rows: List[Tuple[float, float, float]] = []
            for strand, bit in zip(s.strands, ROLE_BITS):
                pole = _pole(s.canonical_mask, bit)
                h_fields.append((HX_MAX * s.fog, 0.0, HZ_MAX * written * pole))
                # Written text starts collapsed at canon; fog starts unwritten
                # (z near 0) with a whisper of transverse coherence.
                init_rows.append((0.1 * s.fog, 0.0, INIT_Z_WRITTEN * written * pole))
            zones.append(
                ZoneSpec(
                    name=s.name,
                    roles=s.strand_names,
                    h_fields=tuple(h_fields),
                    zz=(((0, 1), INTRA_ZZ), ((1, 2), INTRA_ZZ)),
                    gamma=GAMMA,
                    dt=DT,
                    init_bloch=tuple(init_rows),
                    role_modes=ROLE_MODES,
                )
            )

        bridges = tuple(
            BridgeSpec(
                src_zone=l.src_stage,
                src_role=l.src_strand,
                dst_zone=l.dst_stage,
                dst_role=l.dst_strand,
                alpha=l.alpha,
            )
            for l in root.links
        )

        # Quest per stage = the LAST required-beat waypoint in that stage
        # (or the canonical mask when no beat lands there). Core victory()
        # therefore means "every chapter ends where the story demands".
        final_wp: Dict[str, int] = {s.name: s.canonical_mask for s in stages}
        for b in root.beats:
            if not b.required:
                continue
            for stage_name, mask in b.waypoints:
                final_wp[stage_name] = mask
        quests = tuple(QuestSpec(zone=s.name, target_mask=final_wp[s.name]) for s in stages)

        world = WorldSpec(
            spec_id=f"{root.story_id}.world",
            topology_version="story.q3.v1",
            zones=tuple(zones),
            bridges=bridges,
            quests=quests,
            attention=root.attention,
        )
        world_errors = world.validate()
        if world_errors:
            raise ValueError(
                f"story {root.story_id!r} compiled to invalid WorldSpec: "
                + "; ".join(world_errors)
            )
        return world


def compile_story(story: StorySpec) -> WorldSpec:
    return StoryCompiler().compile_hierarchy(story)
