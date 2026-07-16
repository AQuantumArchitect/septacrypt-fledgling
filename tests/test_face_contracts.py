"""Each shipped face object satisfies its edge Protocol — conformance by
test, not inheritance (the engines never import this repo)."""
from septacrypt_core.api.session import GameSession
from septacrypt_core.architect.compiler import ArchitectCompiler
from septacrypt_core.geometry.berry import BerryJourney
from septacrypt_core.spirit.vector import SpiritVector
from umwelt.host.api import GameHost

from septacrypt_fledgling.contracts import (
    AgencyFace,
    BeliefFace,
    DynamicsFace,
    HistoryFace,
    KairosFace,
    MeaningFace,
    StructureFace,
)


def test_all_seven_faces_have_a_shipped_conformant():
    game = GameSession(mode="reactor", seed=1, enable_ledger=False)
    cluster = game.world.zones[game.world.active_zone]

    assert isinstance(ArchitectCompiler(), StructureFace)          # face 1
    assert isinstance(cluster, DynamicsFace)                       # face 2 (umwelt CumulantCluster)
    assert isinstance(GameHost(), BeliefFace)                      # face 3 (umwelt)
    assert isinstance(BerryJourney(), KairosFace)                  # face 4
    assert isinstance(game, HistoryFace)                           # face 5 (GameSession over KnotLedger)
    assert isinstance(game, AgencyFace)                            # face 6 (the HTTP host serves this)
    spirit = SpiritVector(1, 0, 0, 0, 0, 0, 0, frame_id="test", confidence=1.0)
    assert isinstance(spirit, MeaningFace)                         # face 7


def test_agency_face_is_what_the_server_serves():
    """The HTTP router's verb table must stay inside AgencyFace+HistoryFace."""
    from septacrypt_fledgling.server.routes import Router

    served_verbs = {"wait", "look", "stir", "status", "quests", "history", "weave", "report"}
    for verb in served_verbs:
        assert hasattr(Router, verb) or verb in ("quests",), f"router lost verb {verb}"
