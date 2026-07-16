"""StoryCompiler gates: valid WorldSpec, fog->fields monotone, physics runs."""
import numpy as np

from septacrypt_core.api.session import GameSession
from septacrypt_fledgling.contracts import StructureFace
from septacrypt_fledgling.story.compile import StoryCompiler, compile_story
from septacrypt_fledgling.story.starpod import STAR_POD

WORLD = compile_story(STAR_POD)


def test_compiles_to_valid_worldspec():
    assert WORLD.validate() == []
    assert [z.name for z in WORLD.zones] == [s.name for s in sorted(STAR_POD.stages, key=lambda s: s.order)]
    assert len(WORLD.bridges) == len(STAR_POD.links)
    assert len(WORLD.quests) == len(STAR_POD.stages)


def test_story_compiler_is_structure_face():
    assert isinstance(StoryCompiler(), StructureFace)


def test_fog_to_fields_monotone():
    by_name = {z.name: z for z in WORLD.zones}
    egg, aegis = by_name["Egg"], by_name["Aegis"]
    # fog drives transverse hx; written-ness drives |hz|
    assert egg.h_fields[0][0] < aegis.h_fields[0][0]
    assert abs(egg.h_fields[0][2]) > abs(aegis.h_fields[0][2])
    # written chapters boot collapsed at canon; fog boots near the equator
    assert abs(egg.init_bloch[0][2]) > 0.8
    assert abs(aegis.init_bloch[0][2]) < 0.2


def test_quests_are_final_waypoints():
    quest = {q.zone: q.target_mask for q in WORLD.quests}
    assert quest["Shepherd"] == 0b111   # necrotech-choice ends reintegrated
    assert quest["Cleave"] == 0b110     # canon leaves Earth unresolved
    assert quest["Egg"] == 0b111


def test_written_canon_persists_and_fog_shimmers():
    g = GameSession(spec=WORLD, seed=7, enable_ledger=False)
    for _ in range(6):
        g.wait(steps=5)
    egg_z = [abs(g.world.zones["Egg"].role_bloch(r)[2]) for r in ("hacker", "machine", "crowd")]
    assert min(egg_z) > 0.6, f"canon should persist, got {egg_z}"
    assert g._ground_mask("Egg") == 0b111
    cleave_z = [abs(g.world.zones["Cleave"].role_bloch(r)[2]) for r in ("seed", "ring", "earth")]
    assert max(cleave_z) < 0.6, f"fog should shimmer, got {cleave_z}"


def test_compiled_world_is_deterministic():
    hashes = []
    for _ in range(2):
        g = GameSession(spec=WORLD, seed=13, enable_ledger=True, private_observers=True)
        for _ in range(4):
            g.wait(steps=5)
        g.look("player", "human", zone="Shepherd")
        g.wait(steps=5)
        hashes.append(g.physics_hash())
    assert hashes[0] == hashes[1]
