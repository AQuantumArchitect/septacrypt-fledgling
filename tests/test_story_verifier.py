"""StoryVerifier unit gates: ink, continuity law, beats, viability.

Uses a FakeGame so each rule is exercised deterministically; the physics-
coupled behavior is gated in test_story_session / the story proof.
"""
import numpy as np

from septacrypt_fledgling.story.spec import (
    BeatSpec,
    StageSpec,
    StorySpec,
    StrandSpec,
)
from septacrypt_fledgling.story.verifier import INK_THRESHOLD, ROLE_BITS, StoryVerifier


class FakeZone:
    def __init__(self, roles):
        self.roles = list(roles)
        self.z = {r: 0.0 for r in roles}

    def role_bloch(self, role):
        return np.array([0.0, 0.0, self.z[role]])


class FakeGame:
    def __init__(self, stages):
        self.world = type("W", (), {})()
        self.world.zones = {s.name: FakeZone(s.strand_names) for s in stages}

    def set_z(self, stage, strand, z):
        self.world.zones[stage].z[strand] = z


def _stage(name="Alpha", order=0, canonical=0b111, forbidden=(0b000, 0b010)):
    return StageSpec(
        name=name, order=order, era="t",
        strands=(StrandSpec("a", "u", "d"), StrandSpec("b", "u", "d"), StrandSpec("c", "u", "d")),
        canonical_mask=canonical,
        allowed_masks=tuple(m for m in range(8) if m not in forbidden),
        forbidden_masks=tuple(forbidden),
        fog=0.5,
    )


def _setup(beats=()):
    stage = _stage()
    story = StorySpec(story_id="t", version="1", stages=(stage,), beats=tuple(beats))
    assert story.validate() == []
    return StoryVerifier(story), FakeGame((stage,))


def test_ink_only_on_touched_strand_and_threshold():
    v, g = _setup()
    g.set_z("Alpha", "a", -0.9)
    g.set_z("Alpha", "b", -0.9)
    assert v.check(g, touched=("Alpha", "a")).coherent
    assert v.inked_strands("Alpha") == {"a": -1, "b": 0, "c": 0}  # b untouched
    g.set_z("Alpha", "c", INK_THRESHOLD / 2)
    assert v.check(g, touched=("Alpha", "c")).coherent
    assert v.inked_strands("Alpha")["c"] == 0  # below threshold: not written


def test_effective_mask_defaults_to_canon():
    v, g = _setup()
    assert v.effective_mask("Alpha") == 0b111
    g.set_z("Alpha", "a", -0.9)
    v.check(g, touched=("Alpha", "a"))
    assert v.effective_mask("Alpha") == 0b011


def test_forbidden_mask_corrupts_with_named_rule():
    v, g = _setup()
    g.set_z("Alpha", "a", -0.9)
    assert v.check(g, touched=("Alpha", "a")).coherent   # 011 legal
    g.set_z("Alpha", "c", -0.9)
    verdict = v.check(g, touched=("Alpha", "c"))          # -> 010 forbidden
    assert not verdict.coherent
    assert verdict.rule == "forbidden-mask"
    assert "Mal_Gnosis" in verdict.reason and verdict.stage == "Alpha"


def test_beats_require_full_ink_not_presumed_canon():
    beats = (BeatSpec("home", "stay", (("Alpha", 0b111),)),)
    v, g = _setup(beats)
    # effective mask already equals the waypoint, but nothing is written yet
    assert v.check(g).coherent
    assert v.cursor == 0
    for strand in ("a", "b", "c"):
        g.set_z("Alpha", strand, 0.9)
        v.check(g, touched=("Alpha", strand))
    assert v.cursor == 1
    assert v.beats_complete()


def test_stranded_waypoint_corrupts():
    # Legal set is only {101, 011}: once the telling stands at 101, the beat
    # waypoint 011 is Hamming-2 with no legal bridge state — stranded.
    stage = _stage(forbidden=(0b000, 0b001, 0b010, 0b100, 0b110, 0b111))
    story = StorySpec(story_id="t2", version="1",
                      stages=(stage,), beats=(BeatSpec("b", "x", (("Alpha", 0b011),)),))
    v = StoryVerifier(story)
    g = FakeGame((stage,))
    for strand, z in (("a", 0.9), ("b", -0.9), ("c", 0.9)):
        g.set_z("Alpha", strand, z)
        v.check(g, touched=("Alpha", strand))
    verdict = v.check(g)
    assert not verdict.coherent
    assert verdict.rule == "beat-unreachable"


def test_legal_next_masks_one_step_within_legal():
    v, g = _setup()
    assert sorted(v.legal_next_masks("Alpha")) == [0b011, 0b101, 0b110]  # not 010
