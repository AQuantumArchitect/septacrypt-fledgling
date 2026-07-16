"""StorySession gates: journal, boot ink, corruption refusal, revival proof.

Seed 7 is the pinned scenario seed (same as the story proof): the scripted
read sequences below are deterministic under it.
"""
import pytest

from septacrypt_fledgling.story.session import StorySession, TransmissionCorrupted
from septacrypt_fledgling.story.starpod import STAR_POD

SEED = 7


def _ink(s, stage, strand, sign, budget=16):
    """Read a strand until it inks with the wanted sign (waiting out the
    shimmer rotation between attempts)."""
    for _ in range(budget):
        r = s.choose(stage, strand)
        if s.run_state == "corrupted":
            return False
        if r["inked"][strand] == sign:
            return True
        s.wait(steps=12)
        if s.run_state == "corrupted":
            return False
    return False


@pytest.fixture(scope="module")
def corrupted_session():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=5)
    assert _ink(s, "Shepherd", "ai", +1)
    assert _ink(s, "Shepherd", "human", -1)
    _ink(s, "Shepherd", "robot", -1)  # inking 010 IS the corruption
    assert s.run_state == "corrupted"
    return s


def test_boot_reads_the_written_book():
    s = StorySession(STAR_POD, seed=SEED)
    assert s.run_state == "coherent"
    # the four written chapters attest their beats by existing
    assert s.completed_beats[:4] == [
        "egg-merger", "gestation-prometheus", "birth-outbourne", "orbit-fracture"]
    assert s.verifier.inked_strands("Egg") == {"hacker": 1, "machine": 1, "crowd": 1}
    # the deep fog is unwritten
    assert s.verifier.inked_strands("Cleave") == {"seed": 0, "ring": 0, "earth": 0}


def test_journal_records_every_play_verb_and_hash():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    s.choose("Aegis", "entity")
    s.stir()
    assert [e["verb"] for e in s.journal] == ["wait", "choose", "stir"]
    assert all(e["physics_hash"] for e in s.journal)
    assert s.last_coherent == 3


def test_verifier_never_touches_physics():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    h = s.physics_hash()
    for _ in range(3):
        s.verifier.check(s.game, touched=("Cleave", "seed"))
    assert s.physics_hash() == h


def test_corrupted_run_refuses_play_verbs(corrupted_session):
    s = corrupted_session
    for call in (
        lambda: s.wait(),
        lambda: s.choose("Egg", "hacker"),
        lambda: s.look("player", "seed", zone="Cleave"),
        lambda: s.stir(),
    ):
        with pytest.raises(TransmissionCorrupted, match="checksum"):
            call()
    # read surface stays open
    assert s.story_state()["run_state"] == "corrupted"
    assert s.history() is not None


def test_corruption_names_rule_and_stage(corrupted_session):
    c = corrupted_session.story_state()["corruption"]
    assert c["rule"] == "forbidden-mask"
    assert c["stage"] == "Shepherd"
    assert "Mal_Gnosis" in c["reason"]
