"""Kairos gates: chapter phase accumulates; loops are detected, never gate."""
from septacrypt_fledgling.story.kairos import chapter_phase
from septacrypt_fledgling.story.session import StorySession
from septacrypt_fledgling.story.starpod import STAR_POD

SEED = 7


def test_chapter_phase_moves_under_wait():
    """Geometric phase is SIGNED (it can wind back) — the gate is that the
    process clock moves at all, not that it is monotone."""
    s = StorySession(STAR_POD, seed=SEED)
    p0 = chapter_phase(s, "Aegis")
    assert p0["total_phase"] == 0.0
    s.wait(steps=10)
    p1 = chapter_phase(s, "Aegis")
    s.wait(steps=10)
    p2 = chapter_phase(s, "Aegis")
    assert p1["total_phase"] != p0["total_phase"]
    assert p2["total_phase"] != p1["total_phase"]
    assert all(v != 0.0 for v in p1["per_role"].values())


def test_loop_detected_on_shimmer_circle_without_beat_progress():
    s = StorySession(STAR_POD, seed=SEED)
    s.choose("Aegis", "entity")  # collapse: a real excursion begins
    looped = False
    for _ in range(8):
        s.wait(steps=9)  # ~quarter shimmer period per wait
        if s.kairos.looping("Aegis"):
            looped = True
            break
    assert looped, "a full shimmer circle with no beat progress must flag as looping"
    # a settled written chapter is NOT looping (static != circling)
    assert not s.kairos.looping("Egg")


def test_looping_never_corrupts_or_gates():
    s = StorySession(STAR_POD, seed=SEED)
    s.choose("Aegis", "entity")
    for _ in range(8):
        s.wait(steps=9)
    assert s.run_state in ("coherent", "complete")  # a loop is a hint, not a law
    st = s.story_state()
    aegis = next(x for x in st["stages"] if x["name"] == "Aegis")
    assert "looping" in aegis["kairos"]
