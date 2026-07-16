"""Spirit gates: reorders legal options, never legalizes anything."""
from septacrypt_fledgling.story.spirit import SpiritFrames
from septacrypt_fledgling.story.starpod import STAR_POD

FRAMES = SpiritFrames(STAR_POD)


def test_spirit_never_legalizes():
    for stage in STAR_POD.stages:
        legal = sorted(set(stage.allowed_masks) - set(stage.forbidden_masks))
        ranked = FRAMES.rank(stage.name, legal)
        for voice, order in ranked.items():
            assert sorted(order) == legal, f"{voice} altered the legal set in {stage.name}"
            assert not set(order) & set(stage.forbidden_masks)


def test_spirit_ranking_is_deterministic():
    legal = [0b011, 0b101, 0b110, 0b111]
    a = FRAMES.rank("Aegis", list(legal))
    b = FRAMES.rank("Aegis", list(legal))
    assert a == b


def test_frames_disagree_somewhere():
    """Different voices genuinely prefer different tellings (else the frames
    carry no meaning)."""
    disagreements = 0
    for stage in STAR_POD.stages:
        legal = sorted(set(stage.allowed_masks) - set(stage.forbidden_masks))
        ranked = FRAMES.rank(stage.name, legal)
        tops = {order[0] for order in ranked.values()}
        if len(tops) > 1:
            disagreements += 1
    assert disagreements >= 1


def test_guard_frame_prefers_the_shield():
    """Guard (honor+might) ranks Aegis 110 (entity+shield standing) above
    011 (no entity) — the shield voice wants the shield raised."""
    ranked = FRAMES.rank("Aegis", [0b011, 0b110])
    assert ranked["guard"][0] == 0b110
