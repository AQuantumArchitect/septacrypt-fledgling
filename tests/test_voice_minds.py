"""Voice minds: coverage masks respected; witnessed readings land privately."""
from septacrypt_fledgling.story.session import StorySession
from septacrypt_fledgling.story.starpod import STAR_POD

SEED = 7


def test_voices_state_respects_coverage():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    s.choose("Aegis", "containment")
    v = s.voices_state()
    assert set(v) == {"guard", "translator", "seer", "rasi"}  # paul observes nothing
    # guard's surfaced beliefs are exactly its covered channels
    guard_cov = {f"{st}_{sd}" for st, sd in
                 next(x for x in STAR_POD.voices if x.name == "guard").observes}
    assert set(v["guard"]["beliefs"]) <= guard_cov
    assert "Aegis_containment" in v["guard"]["beliefs"]
    # translator covers everything
    assert "Egg_hacker" in v["translator"]["beliefs"]
    # rasi does not witness Egg
    assert not any(k.startswith("Egg_") for k in v["rasi"]["beliefs"])
    for voice in v.values():
        for b in voice["beliefs"].values():
            assert -1.0 <= b["z"] <= 1.0 and 0.0 <= b["confidence"] <= 1.0


def test_witness_only_on_covered_reads():
    s = StorySession(STAR_POD, seed=SEED)
    # Egg.hacker is covered by the translator only (guard covers Egg.crowd)
    cov = s._voice_coverage
    assert [v.name for v in cov[("Egg", "hacker")]] == ["translator"]
    assert {v.name for v in cov[("Aegis", "containment")]} >= {"guard", "translator", "seer", "rasi"}


def test_minds_ride_outside_physics():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    s.choose("Aegis", "entity")
    h = s.physics_hash()
    s.voices_state()   # syncing/reading minds must not move the world
    s.voices_state()
    assert s.physics_hash() == h
