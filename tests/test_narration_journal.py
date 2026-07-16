"""Narration rides OUTSIDE the physics: hash-invariant, replay-reusable."""
from septacrypt_fledgling.story.session import StorySession
from septacrypt_fledgling.story.starpod import STAR_POD

from test_story_session import _ink

SEED = 7


def test_narration_never_changes_physics_hash():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    h = s.physics_hash()
    for voice in ("rasi", "guard", "seer", "translator", "paul"):
        s.narrate(voice=voice)
    assert s.physics_hash() == h


def test_same_actions_with_and_without_narration_hash_identical():
    def run(narrate):
        s = StorySession(STAR_POD, seed=SEED)
        s.wait(steps=3)
        s.choose("Aegis", "entity")
        if narrate:
            s.narrate(voice="rasi")
        s.wait(steps=3)
        return s.physics_hash()

    assert run(False) == run(True)


def test_revival_replay_reuses_narration_verbatim():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=5)
    _ink(s, "Shepherd", "ai", +1)
    _ink(s, "Shepherd", "human", -1)
    _ink(s, "Shepherd", "robot", -1)  # corrupt
    assert s.run_state == "corrupted"
    s.revive()
    before = s.narrate(voice="rasi")  # narrated at the fork stamp
    n_before = len(s.narration())

    # Stray the SAME way from the fork: RNG state there is identical, so the
    # trajectory, the corruption point, and the revival stamp all repeat —
    # and the narration cache returns the prose verbatim, no new entry.
    _ink(s, "Shepherd", "robot", -1)
    assert s.run_state == "corrupted"
    s.revive()
    after = s.narrate(voice="rasi")
    assert after == before
    assert len(s.narration()) == n_before

    # journal chronology is servable incrementally
    entries = s.narration()
    assert entries, "journal empty"
    since = s.narration(since=entries[0]["stamp_id"])
    assert len(since) == len(entries) - 1
