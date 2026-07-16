"""Manuscript ingest gates against the real archived index.html."""
from septacrypt_fledgling.story.ingest import (
    STAGE_NAMES,
    ingest_manuscript,
    stage_fog,
)

RESULT = ingest_manuscript()


def test_layer_census_matches_manuscript():
    c = RESULT.layer_census
    assert c["myth"] == 88
    assert c["translator"] == 37
    assert c["guard"] == 32
    assert c["seer"] == 10
    assert c["appendix"] == 62
    assert c["outline"] == 4


def test_all_seven_stages_have_passages():
    for name in STAGE_NAMES:
        assert RESULT.stage_passages(name), f"stage {name} empty"


def test_stubs_are_flagged():
    for name in ("Aegis", "Shepherd", "Cleave"):
        ps = RESULT.stage_passages(name)
        assert all(p.stub for p in ps), f"{name} should be pure outline stubs"
    assert not any(p.stub for p in RESULT.stage_passages("Egg"))


def test_rs_markers_extracted():
    # Gestation's heading carries [R2S0]; its passages inherit it.
    gest = RESULT.stage_passages("Gestation")
    assert any(p.rs_removal == 2 for p in gest)
    # The Conviction section inside Gestation is [R3S1].
    assert any(p.rs_removal == 3 and p.rs_speculation == 1 for p in gest)


def test_corruption_flagged():
    # "Proto-Life" contains Guard reconstruction blocks nested in myth spans.
    egg_like = [p for p in RESULT.passages if p.corrupted]
    assert egg_like, "no corrupted passages found"
    assert any(p.voice == "myth" for p in egg_like)


def test_fog_ordering():
    fogs = {name: stage_fog(RESULT.stage_passages(name)) for name in STAGE_NAMES}
    for written in ("Egg", "Gestation", "Birth", "Orbit"):
        assert fogs[written] < 0.2, f"{written} fog {fogs[written]}"
    for stub in ("Aegis", "Shepherd", "Cleave"):
        assert fogs[stub] > 0.7, f"{stub} fog {fogs[stub]}"
