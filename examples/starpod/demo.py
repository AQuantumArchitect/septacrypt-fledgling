"""STAR POD — the whole book over the real HTTP API, narrated.

Usage: python examples/starpod/demo.py [--seed 7] [--voice rasi]

Plays the transmission end to end: the written chapters attest themselves,
the reader collapses the fog (Aegis, Shepherd, Cleave), strays once into a
forbidden telling (Mal_Gnosis — the run corrupts), revives from the last
coherent stamp with a physics-hash fork proof, and reads on to victory.
Narration is pulled after each beat (offline register-true fallback unless
NARRATOR_MODE=api and ANTHROPIC_API_KEY are set).

Deterministic at a fixed seed: same seed, same choices, same book.
"""
import argparse
import json
import sys
import threading
import urllib.error
import urllib.request

sys.path.insert(0, "src")

from septacrypt_fledgling.server.app import make_server  # noqa: E402


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return json.loads(err.read())


def ink(base, sid, stage, strand, sign, budget=16):
    """Read a strand until it inks the wanted way; wait out the shimmer
    rotation between attempts. Returns the final run_state."""
    for _ in range(budget):
        r = call(base, "POST", f"/v1/sessions/{sid}/choose",
                 {"stage": stage, "strand": strand})
        if not r.get("ok"):
            return "corrupted"
        state = r["result"]["run_state"]
        if state == "corrupted" or r["result"]["inked"][strand] == sign:
            return state
        call(base, "POST", f"/v1/sessions/{sid}/wait", {"steps": 12})
    return "stuck"


def narrate(base, sid, voice):
    r = call(base, "POST", f"/v1/sessions/{sid}/narrate", {"voice": voice})
    n = r["narration"]
    print(f'    ~ [{n["voice"]}/{n["source"]}] {n["text"]}\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--voice", default="rasi")
    args = parser.parse_args()

    server = make_server(port=0)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("=== STAR POD: A TRANSMISSION, PARTLY WRITTEN ===\n")
    sid = call(base, "POST", "/v1/sessions", {"story": "starpod", "seed": args.seed})["session_id"]

    story = call(base, "GET", f"/v1/sessions/{sid}/story")["story"]
    print(f"The written chapters attest themselves: {', '.join(story['beats']['completed'])}")
    fogs = {s["name"]: s["fog"] for s in story["stages"]}
    print(f"Fog: Egg {fogs['Egg']:.2f} … Aegis {fogs['Aegis']:.2f} — "
          "the last three chapters are unwritten.\n")
    call(base, "POST", f"/v1/sessions/{sid}/wait", {"steps": 5})
    narrate(base, sid, "paul")

    print("-- AEGIS: the shield must rise before the poison is contained --")
    for stage, strand, sign in (("Aegis", "entity", 1), ("Aegis", "shield", 1),
                                ("Aegis", "containment", -1), ("Aegis", "containment", 1)):
        assert ink(base, sid, stage, strand, sign) != "stuck"
    narrate(base, sid, args.voice)

    print("-- SHEPHERD: the reader strays — Mal_Gnosis --")
    ink(base, sid, "Shepherd", "ai", 1)
    ink(base, sid, "Shepherd", "human", -1)
    state = ink(base, sid, "Shepherd", "robot", -1)   # 010: forbidden
    story = call(base, "GET", f"/v1/sessions/{sid}/story")["story"]
    print(f"    run_state: {story['run_state']} — {story['corruption']['reason']}")
    refused = call(base, "POST", f"/v1/sessions/{sid}/wait", {})
    print(f"    a further verb is refused: {refused['error']['kind']}")
    narrate(base, sid, "guard")

    r = call(base, "POST", f"/v1/sessions/{sid}/revive")["result"]
    print(f"    REVIVED on {r['branch_id']}: fork proof "
          f"{r['fork_proof']['replayed'][:12]} == recorded "
          f"({r['fork_proof']['match']}); the dead telling "
          f"{r['corrupted_head_hash'][:12]} is left behind.\n")

    print("-- SHEPHERD, retold: the Necrotech choice --")
    for stage, strand, sign in (("Shepherd", "human", 1), ("Shepherd", "robot", 1),
                                ("Shepherd", "ai", -1), ("Shepherd", "ai", 1)):
        assert ink(base, sid, stage, strand, sign) != "stuck"
    narrate(base, sid, args.voice)

    print("-- CLEAVE: Seed becomes Ring; Earth stays dark --")
    for stage, strand, sign in (("Cleave", "seed", 1), ("Cleave", "ring", 1),
                                ("Cleave", "earth", -1)):
        assert ink(base, sid, stage, strand, sign) != "stuck"

    story = call(base, "GET", f"/v1/sessions/{sid}/story")["story"]
    print(f"\nrun_state: {story['run_state']} | victory: {story['victory']} | "
          f"beats {story['beats']['cursor']}/{story['beats']['total_waypoints']}")
    voices = call(base, "GET", f"/v1/sessions/{sid}/voices")["voices"]
    seer_cleave = {k: v["z"] for k, v in voices["seer"]["beliefs"].items() if "Cleave" in k}
    print(f"the Seer's private beliefs about Cleave: {seer_cleave}")
    narrate(base, sid, "seer")

    hist = call(base, "GET", f"/v1/sessions/{sid}/history")
    print(f"the collapsed book: {len(hist['history'])} stamps, "
          f"checksum {hist['physics_hash'][:16]}…")
    branches = call(base, "GET", f"/v1/sessions/{sid}/branches")["branches"]
    print(f"the tellings that died: {[b['branch_id'] for b in branches]}")

    server.shutdown()
    print("\n=== TRANSMISSION COMPLETE — Rejoyce those within the shell. ===")


if __name__ == "__main__":
    main()
