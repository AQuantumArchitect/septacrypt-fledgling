"""StorySpec validation + narrative (beat) closure."""
import dataclasses

import pytest

from septacrypt_fledgling.story.spec import (
    BeatSpec,
    StageSpec,
    StorySpec,
    StrandSpec,
)
from septacrypt_fledgling.story.starpod import STAR_POD


def _stage(name="Alpha", order=0, canonical=0b111, allowed=None, forbidden=(0b000,)):
    return StageSpec(
        name=name,
        order=order,
        era="test",
        strands=(StrandSpec("a", "u", "d"), StrandSpec("b", "u", "d"), StrandSpec("c", "u", "d")),
        canonical_mask=canonical,
        allowed_masks=tuple(allowed) if allowed is not None
        else tuple(m for m in range(8) if m not in forbidden),
        forbidden_masks=tuple(forbidden),
        fog=0.5,
    )


def _story(stages, beats=()):
    return StorySpec(story_id="t.v1", version="1", stages=stages, beats=tuple(beats))


def test_starpod_validates():
    assert STAR_POD.validate() == []


def test_starpod_shape():
    assert [s.name for s in STAR_POD.stages] == [
        "Egg", "Gestation", "Birth", "Orbit", "Aegis", "Shepherd", "Cleave"]
    assert all(len(s.strands) == 3 for s in STAR_POD.stages)
    # fog: written chapters clear, stubs deep
    assert STAR_POD.stage("Egg").fog < 0.2 < STAR_POD.stage("Aegis").fog
    # every stage forbids total erasure
    assert all(0b000 in s.forbidden_masks for s in STAR_POD.stages)
    beat_ids = [b.beat_id for b in STAR_POD.beats]
    assert "necrotech-choice" in beat_ids and "cleave-return" in beat_ids


def test_validator_catches_structural_errors():
    two_strands = dataclasses.replace(
        _stage(), strands=(StrandSpec("a", "u", "d"), StrandSpec("b", "u", "d")))
    assert any("exactly 3" in e for e in _story((two_strands,)).validate())

    bad_canon = _stage(canonical=0b000)  # canonical inside forbidden -> not allowed
    assert any("canonical_mask not in allowed" in e for e in _story((bad_canon,)).validate())

    overlap = dataclasses.replace(_stage(), allowed_masks=(0b000, 0b111))
    assert any("both allowed and forbidden" in e for e in _story((overlap,)).validate())


def test_beat_closure_catches_unreachable_waypoint():
    # Only canon and its antipode are allowed: 111 -> 000-blocked island 001? No:
    # allowed {111, 001} — Hamming distance 2 with no intermediate = unreachable.
    island = _stage(allowed=(0b111, 0b001), forbidden=())
    beats = (BeatSpec("jump", "teleport", (("Alpha", 0b001),)),)
    errors = _story((island,), beats).validate()
    assert any("narrative closure fails" in e for e in errors)


def test_beat_closure_walks_waypoints_in_sequence():
    stage = _stage()
    beats = (
        BeatSpec("there", "out", (("Alpha", 0b110),)),
        BeatSpec("back", "home", (("Alpha", 0b111),)),
    )
    assert _story((stage,), beats).validate() == []


def test_beats_out_of_chronological_order_rejected():
    s0, s1 = _stage("A", 0), _stage("B", 1)
    beats = (BeatSpec("rev", "reversed", (("B", 0b111), ("A", 0b111))),)
    errors = _story((s0, s1), beats).validate()
    assert any("chronological" in e for e in errors)
