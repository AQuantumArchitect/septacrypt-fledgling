"""M2.4 parity probe: umwelt WorldSession vs septacrypt ObserverBeliefStore.

The Keith & Dwayne scenario (plan §12 steps 2-5): the valve closes; Dwayne
observes it, Keith does not. Both backends must hold correctly DIVERGENT
private beliefs: Dwayne knows the valve is closed (z < 0), Keith still
believes it open (z >= 0), and nothing about Dwayne's look leaks into Keith.
"""
from septacrypt_core.api.session import GameSession
from septacrypt_core.ledger.events import measure_event

from septacrypt_fledgling.minds.adapter import UmweltMindsAdapter

ROLES = ("valve_17", "coolant_pump", "temp_sensor")


def _septacrypt_backend():
    """Drive the same scenario through GameSession's belief store."""
    g = GameSession(mode="reactor", seed=7, enable_ledger=False, private_observers=True)
    zone = g.world.active_zone
    # Let the reactor drift off its boot pole first: at exactly |z|=1 the
    # Belavkin measurement gain is zero (1-z^2 = 0) and no observation can
    # move the ground — the absorbing-state fact, not a test artifact.
    for _ in range(10):
        g.wait()
    # Both observers exist and have baseline beliefs.
    g.beliefs.ensure("keith", g.world)
    g.beliefs.ensure("dwayne", g.world)
    # The valve-close event, witnessed by Dwayne only (a LOOK with a forced
    # outcome, applied through the same typed event path look() uses).
    ev = measure_event("valve_17", -1.0, zone=zone, strength=1.0, observer_id="dwayne")
    g._run((ev,), observer_id="dwayne", event_kind="look", scale=(zone, "valve_17"))
    keith_z = g.beliefs.bloch("keith", zone, "valve_17", g.world)[2]
    dwayne_z = g.beliefs.bloch("dwayne", zone, "valve_17", g.world)[2]
    return keith_z, dwayne_z


def _umwelt_backend():
    minds = UmweltMindsAdapter(ROLES)
    minds.add_observer("keith")
    minds.add_observer("dwayne")
    # Everyone initially saw the valve open (shared prior).
    for who in ("keith", "dwayne"):
        minds.saw(who, "valve_17", +1.0, confidence=0.9)
    minds.step()
    # The valve closes; only Dwayne sees it. Read right after the sighting —
    # unobserved beliefs relax toward their prior over further steps, which
    # is the engine's honesty, not a bug.
    minds.saw("dwayne", "valve_17", -1.0, confidence=1.0)
    keith = minds.belief_z("keith", "valve_17")
    dwayne = minds.belief_z("dwayne", "valve_17")
    assert keith is not None and dwayne is not None
    return keith[0], dwayne[0]


def test_keith_dwayne_divergence_parity():
    for backend, (keith_z, dwayne_z) in (
        ("septacrypt", _septacrypt_backend()),
        ("umwelt", _umwelt_backend()),
    ):
        assert dwayne_z < 0, f"{backend}: Dwayne should believe valve closed, z={dwayne_z}"
        assert keith_z >= 0, f"{backend}: Keith should still believe valve open, z={keith_z}"
        assert dwayne_z < keith_z, f"{backend}: beliefs failed to diverge"


def test_report_updates_target_only_in_umwelt_backend():
    minds = UmweltMindsAdapter(ROLES)
    for who in ("keith", "dwayne", "bystander"):
        minds.add_observer(who)
    minds.saw("dwayne", "valve_17", -1.0, confidence=1.0)
    # Dwayne tells Keith; the bystander hears nothing.
    minds.heard("keith", "valve_17", -1.0, confidence=0.6)
    keith = minds.belief_z("keith", "valve_17")
    dwayne = minds.belief_z("dwayne", "valve_17")
    bystander = minds.belief_z("bystander", "valve_17")
    assert keith is not None and dwayne is not None and bystander is not None
    # A heard report moves the target toward the truth but with less
    # conviction than the eyewitness; the bystander stays most positive.
    assert dwayne[0] < keith[0] < bystander[0]
