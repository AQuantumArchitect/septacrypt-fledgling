"""ADR-001 name hygiene: the host namespace must never export the four
collision-hazard names that umwelt and septacrypt-core both define
incompatibly, nor re-export GameSession itself."""
import septacrypt_fledgling

HAZARD_NAMES = ("GameHost", "WorldSession", "Observation", "Intent", "GameSession")


def test_no_hazard_exports():
    for name in HAZARD_NAMES:
        assert not hasattr(septacrypt_fledgling, name), f"{name} leaked into host namespace"
    for name in HAZARD_NAMES:
        assert name not in getattr(septacrypt_fledgling, "__all__", ())
