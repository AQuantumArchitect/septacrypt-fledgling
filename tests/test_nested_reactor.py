"""Nested Reactor / Missing Valve vertical slice — plan §12.4 subset gates.

Scenario (seed 2, deterministic): the Repair Station drifts off its boot
pole; Dwayne LOOKs at valve_17 at t1 and sees it closed; Keith doesn't.
The station mask moves from 111 to 011. Keith investigates: retro candidates
are generated, his probe re-ranks them, the truth ranks first; a valid
Microscope insertion forks the ledger; an invalid one is rejected by name;
spirit frames reorder valid candidates but never legalize anything.
"""
from septacrypt_core.api.session import GameSession
from septacrypt_core.spirit.vector import SpiritVector

from septacrypt_fledgling.minds.adapter import UmweltMindsAdapter
from septacrypt_fledgling.retro import (
    generate_candidates,
    propose_insertion,
    rank_by_belief,
    spirit_rank,
)

ROLES = ("valve_17", "coolant_pump", "temp_sensor")
SEED = 2


def _play_scenario():
    g = GameSession(mode="reactor", seed=SEED, enable_ledger=True, private_observers=True)
    zone = g.world.active_zone
    minds = UmweltMindsAdapter(ROLES)
    minds.add_observer("keith")
    minds.add_observer("dwayne")

    for _ in range(10):
        g.wait()
    checkpoint_mask = g._ground_mask(zone)

    # t1 — the valve event: Dwayne sees it, Keith does not.
    g.look("dwayne", "valve_17", zone=zone)
    valve_z = float(g.world.zones[zone].role_bloch("valve_17")[2])
    minds.saw("dwayne", "valve_17", -1.0 if valve_z < 0 else 1.0)

    # t2 — heat rises; Keith notices the symptom only.
    for _ in range(5):
        g.wait()
    observed_mask = g._ground_mask(zone)
    return g, zone, minds, checkpoint_mask, observed_mask


def test_divergent_minds():
    _, _, minds, _, _ = _play_scenario()
    dwayne = minds.belief_z("dwayne", "valve_17")
    keith = minds.belief_z("keith", "valve_17")
    assert dwayne is not None and dwayne[0] < 0
    assert keith is None or keith[0] > dwayne[0]


def test_candidates_and_probe_reranking():
    g, zone, minds, m0, m2 = _play_scenario()
    assert m0 == 0b111 and m2 == 0b011  # pinned scenario

    candidates = generate_candidates(m0, m2, ROLES)
    labels = [c.label for c in candidates]
    assert len([c for c in candidates if c.path]) >= 3
    assert any("valve_17" in lbl for lbl in labels)
    assert any("unknown" in lbl for lbl in labels)

    # Keith, pre-probe: no belief about the valve — candidates tie near zero.
    keith_beliefs = {}
    pre = rank_by_belief(list(candidates), keith_beliefs, ROLES, m2)

    # Keith probes the valve (the discriminating LOOK).
    g.look("keith", "valve_17", zone=zone)
    keith_valve_z = float(g.world.zones[zone].role_bloch("valve_17")[2])
    minds.saw("keith", "valve_17", -1.0 if keith_valve_z < 0 else 1.0)
    kb = minds.beliefs_snapshot("keith")
    keith_beliefs = {role: z for role, (z, _c) in kb.items()}
    post = rank_by_belief(list(candidates), keith_beliefs, ROLES, m2)

    # Ground truth (valve closed) ranks first after the probe.
    assert "valve_17" in post[0].flipped_roles, f"top candidate was {post[0].label}"
    assert post[0].score > post[-1].score


def test_insertion_accept_fork_and_reject_by_name():
    g, _, _, m0, m2 = _play_scenario()
    pre_heads = dict(g.ledger.branches)

    # Valid Microscope insertion: a maintenance event that walks 111→011.
    ok = propose_insertion(g, start_mask=m0, proposed_path=(0b111, 0b011), branch_id="maintenance")
    assert ok.accepted and ok.branch_id == "maintenance"
    assert g.ledger.branches["maintenance"] == ok.fork_head
    # Fork shares prefix with main: the fork head IS a stamp on main's history.
    main_ids = [s.stamp_id for s in g.ledger.get_history("main")]
    assert ok.fork_head in main_ids
    assert g.ledger.branches["main"] == pre_heads["main"]  # main unmoved

    # Invalid insertion: teleport 111→010 (Hamming 2) must be rejected BY NAME.
    bad = propose_insertion(g, start_mask=m0, proposed_path=(0b111, 0b010))
    assert not bad.accepted
    assert "non-adjacent" in bad.reason and "111->010" in bad.reason


def test_spirit_reorders_but_never_legalizes():
    _, _, _, m0, m2 = _play_scenario()
    candidates = generate_candidates(m0, m2, ROLES)
    valid_paths = {c.path for c in candidates if c.path}

    def frame(**kw):
        base = dict(wisdom=0, might=0, wealth=0, power=0, glory=0, honor=0, blessing=0)
        base.update(kw)
        return SpiritVector(**base, frame_id="t", confidence=1.0)

    # State values: sensor bit reads as wisdom, pump bit as glory — so the
    # two frames prefer genuinely different intermediate histories.
    state_values = {
        m: frame(glory=float(bool(m & 0b010)), wisdom=float(bool(m & 0b001)))
        for m in range(8)
    }
    keith_frame = frame(wisdom=1.0)      # values knowing (sensor bit stays up)
    station_frame = frame(glory=1.0)     # values the pump staying alive

    for f in (keith_frame, station_frame):
        ranked = spirit_rank(list(candidates), f, state_values)
        # never legalizes: exactly the same path set, plus unknown at bottom
        assert {c.path for c in ranked if c.path} == valid_paths
        assert ranked[-1].path == ()
    # reorders: the two frames disagree about the best history
    top_keith = spirit_rank(list(candidates), keith_frame, state_values)[0]
    top_station = spirit_rank(list(candidates), station_frame, state_values)[0]
    assert top_keith.path != top_station.path or len(valid_paths) == 1
