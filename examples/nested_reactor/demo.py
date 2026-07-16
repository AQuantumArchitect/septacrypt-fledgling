"""Nested Reactor / Missing Valve — the plan-§12 vertical slice, narrated.

Usage: python examples/nested_reactor/demo.py [--seed 2]

The game loop (waits, looks, status, history) runs over the real HTTP API —
exactly what a UI would send. The investigation layer (retro candidates,
Microscope insertion, spirit frames) runs in-process on a twin session with
the same seed; exposing those as endpoints is additive post-freeze work.
"""
import argparse
import json
import sys
import threading
import urllib.request

sys.path.insert(0, "src")

from septacrypt_core.api.session import GameSession  # noqa: E402
from septacrypt_core.spirit.vector import SpiritVector  # noqa: E402

from septacrypt_fledgling.minds.adapter import UmweltMindsAdapter  # noqa: E402
from septacrypt_fledgling.retro import (  # noqa: E402
    generate_candidates,
    propose_insertion,
    rank_by_belief,
    spirit_rank,
)
from septacrypt_fledgling.server.app import make_server  # noqa: E402

ROLES = ("valve_17", "coolant_pump", "temp_sensor")


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2)
    args = parser.parse_args()

    server = make_server(port=0, debug=True)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("=== NESTED REACTOR: THE MISSING VALVE ===\n")

    # -- the played game, over HTTP ------------------------------------------
    sid = call(base, "POST", "/v1/sessions", {"mode": "reactor", "seed": args.seed})["session_id"]
    for _ in range(10):
        call(base, "POST", f"/v1/sessions/{sid}/wait", {})
    st = call(base, "GET", f"/v1/sessions/{sid}/status?observer=dwayne")["state"]
    print(f"t0  checkpoint. Station hums: {st['meta']['current_mythos']['emoji']} "
          f"{st['meta']['current_mythos']['name']}")

    look = call(base, "POST", f"/v1/sessions/{sid}/look",
                {"observer_id": "dwayne", "target_role": "valve_17"})
    print(f"t1  Dwayne checks valve_17 …  {look['state']['narrative_log'][-1]}")

    for _ in range(5):
        call(base, "POST", f"/v1/sessions/{sid}/wait", {})
    st = call(base, "GET", f"/v1/sessions/{sid}/status?observer=keith")["state"]
    print(f"t2  Keith feels the heat. His view: {st['meta']['current_mythos']['emoji']} "
          f"{st['meta']['current_mythos']['name']} (he never saw the valve)")

    hist = call(base, "GET", f"/v1/sessions/{sid}/history")
    print(f"    witnessed knot so far: {len(hist['history'])} stamps, "
          f"root {hist['physics_hash'][:12]}…\n")

    # -- the investigation, in-process on a seed-twin session ----------------
    g = GameSession(mode="reactor", seed=args.seed, enable_ledger=True, private_observers=True)
    zone = g.world.active_zone
    minds = UmweltMindsAdapter(ROLES)
    for who in ("keith", "dwayne"):
        minds.add_observer(who)
    for _ in range(10):
        g.wait()
    m0 = g._ground_mask(zone)
    g.look("dwayne", "valve_17", zone=zone)
    valve_z = float(g.world.zones[zone].role_bloch("valve_17")[2])
    minds.saw("dwayne", "valve_17", -1.0 if valve_z < 0 else 1.0)
    for _ in range(5):
        g.wait()
    m2 = g._ground_mask(zone)

    print(f"RETRO: mask went {m0:03b} → {m2:03b}. Keith asks: what happened?")
    candidates = generate_candidates(m0, m2, ROLES)
    for c in rank_by_belief(list(candidates), {}, ROLES, m2):
        print(f"    candidate: {c.label:<28} score {c.score:+.3f}")

    print("\nKeith probes the valve (the discriminating LOOK)…")
    g.look("keith", "valve_17", zone=zone)
    kz = float(g.world.zones[zone].role_bloch("valve_17")[2])
    minds.saw("keith", "valve_17", -1.0 if kz < 0 else 1.0)
    beliefs = {r: z for r, (z, _c) in minds.beliefs_snapshot("keith").items()}
    ranked = rank_by_belief(list(candidates), beliefs, ROLES, m2)
    for c in ranked:
        print(f"    candidate: {c.label:<28} score {c.score:+.3f}")
    print(f"    → Keith's best explanation: {ranked[0].label}\n")

    print("MICROSCOPE: the player proposes an inserted maintenance event…")
    ok = propose_insertion(g, start_mask=m0, proposed_path=(0b111, 0b011), branch_id="maintenance")
    print(f"    valid   111→011 : accepted={ok.accepted} — {ok.reason}")
    bad = propose_insertion(g, start_mask=m0, proposed_path=(0b111, 0b010))
    print(f"    invalid 111→010 : accepted={bad.accepted} — {bad.reason}")
    print(f"    branches now: {sorted(g.ledger.branches)}\n")

    def frame(**kw):
        base_ = dict(wisdom=0, might=0, wealth=0, power=0, glory=0, honor=0, blessing=0)
        base_.update(kw)
        return SpiritVector(**base_, frame_id="demo", confidence=1.0)

    values = {m: frame(glory=float(bool(m & 0b010)), wisdom=float(bool(m & 0b001))) for m in range(8)}
    keith_top = spirit_rank(list(candidates), frame(wisdom=1.0), values)[0]
    station_top = spirit_rank(list(candidates), frame(glory=1.0), values)[0]
    print("SPIRIT: the same legal histories, under two value frames:")
    print(f"    Keith's frame (wisdom)  favors: {keith_top.label}")
    print(f"    Station's frame (glory) favors: {station_top.label}")
    print("    (spirit reorders legal options; it never legalizes an invalid one)")

    server.shutdown()
    print("\n=== SLICE COMPLETE ===")


if __name__ == "__main__":
    main()
