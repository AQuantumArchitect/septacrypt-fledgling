"""Revival = rebuild + replay, proven by physics-hash equality at the fork."""
import pytest

from septacrypt_fledgling.story.session import StorySession, TransmissionCorrupted
from septacrypt_fledgling.story.starpod import STAR_POD

from test_story_session import _ink

SEED = 7


def _corrupt(s):
    assert _ink(s, "Shepherd", "ai", +1)
    assert _ink(s, "Shepherd", "human", -1)
    _ink(s, "Shepherd", "robot", -1)  # inking 010 IS the corruption
    assert s.run_state == "corrupted"


def test_revive_forks_with_hash_proof_and_plays_on():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=5)
    _corrupt(s)
    coherent_len = s.last_coherent
    dead_hash = s.physics_hash()

    out = s.revive()
    assert out["fork_proof"]["match"] is True
    assert out["fork_proof"]["replayed"] == out["fork_proof"]["recorded"]
    assert out["forked_at_index"] == coherent_len
    assert out["corrupted_head_hash"] == dead_hash
    assert s.run_state == "coherent"
    assert len(s.journal) == coherent_len
    assert s.physics_hash() != dead_hash  # the dead telling is gone

    # RNG state at the fork is identical — the player must choose DIFFERENTLY
    assert _ink(s, "Shepherd", "human", +1)
    assert s.run_state == "coherent"
    assert [r.branch_id for r in s.revivals] == ["revival-1"]
    assert s.revivals[0].corruption_reason.startswith("the Shepherd telling")


def test_second_corruption_forks_again():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=5)
    _corrupt(s)
    s.revive()
    _corrupt(s)  # stray the same way again on the new branch
    s.revive()
    assert [r.branch_id for r in s.revivals] == ["revival-1", "revival-2"]
    assert s.run_state == "coherent"


def test_revive_on_coherent_run_is_an_error():
    s = StorySession(STAR_POD, seed=SEED)
    with pytest.raises(ValueError, match="corrupted"):
        s.revive()
