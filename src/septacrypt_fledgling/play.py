"""STAR POD player client — single-shot commands over the HTTP API.

    python -m septacrypt_fledgling play new [--seed N]   start a game (spawns a server if needed)
    python -m septacrypt_fledgling play look             where the story stands
    python -m septacrypt_fledgling play read STAGE STRAND   read (collapse) one strand
    python -m septacrypt_fledgling play wait [STEPS]     let the transmission play on (default 12)
    python -m septacrypt_fledgling play tell [VOICE]     hear the latest narration (default rasi)
    python -m septacrypt_fledgling play revive           after corruption: restore the last coherent telling
    python -m septacrypt_fledgling play end              end the game

Session state lives in ./.starpod.json so each command is stateless from the
shell's point of view — friendly to humans and agents alike.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

STATE_FILE = Path(".starpod.json")


# -- plumbing -----------------------------------------------------------------
def _call(base: str, method: str, path: str, body: Optional[Dict[str, Any]] = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return json.loads(err.read())


def _server_alive(base: str) -> bool:
    try:
        return bool(_call(base, "GET", "/v1/schema").get("ok"))
    except Exception:
        return False


def _spawn_server() -> str:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.Popen(
        [sys.executable, "-m", "septacrypt_fledgling", "serve", "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        if _server_alive(base):
            return base
        time.sleep(0.2)
    raise SystemExit("could not start the game server")


def _load() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        raise SystemExit("no game in progress — start one with: play new")
    st = json.loads(STATE_FILE.read_text())
    if not _server_alive(st["base"]):
        raise SystemExit("the game server is gone — start a new game with: play new")
    return st


def _story(st: Dict[str, Any]) -> Dict[str, Any]:
    r = _call(st["base"], "GET", f"/v1/sessions/{st['session_id']}/story")
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    return r["story"]


# -- rendering ------------------------------------------------------------------
_INK = {1: "+", -1: "-", 0: "?"}


def _mask_wants(stage: Dict[str, Any], mask: int) -> str:
    bits = (0b100, 0b010, 0b001)
    return " ".join(
        f"{name}{'+' if mask & bit else '-'}"
        for name, bit in zip(stage["strands"], bits)
    )


def _render_look(story: Dict[str, Any], attention: Optional[float] = None) -> None:
    beats = story["beats"]
    print(f"RUN: {story['run_state']} | beats {beats['cursor']}/{beats['total_waypoints']}"
          + (f" | attention {attention:.0f}" if attention is not None else ""))
    if story["corruption"]:
        print(f"!! CORRUPTED: {story['corruption']['reason']}")
        print("!! restore the last coherent telling with: play revive")
    nxt = beats["next_waypoint"]
    stages_by_name = {s["name"]: s for s in story["stages"]}
    if nxt:
        stage = stages_by_name[nxt["stage"]]
        print(f"NEXT BEAT: {nxt['beat_id']} — in {nxt['stage']}, the telling must read: "
              f"{_mask_wants(stage, nxt['mask'])} (every strand read at least once)")
    elif story["victory"]:
        print("THE TRANSMISSION IS COMPLETE — Rejoyce those within the shell.")
    for s in story["stages"]:
        kind = "written" if s["fog"] < 0.3 else "UNWRITTEN"
        parts = []
        for k, v in s["inked"].items():
            lean = s["lean"][k]
            arrow = "" if kind == "written" else (
                "↑" if lean > 0.15 else ("↓" if lean < -0.15 else "~"))
            parts.append(f"{k}{_INK[v]}{arrow}")
        is_next = bool(nxt and s["name"] == nxt["stage"])
        marker = "  <— next beat" if is_next else ""
        # the circles hint only matters where the story is actually stuck
        loop = ("  (going in circles — the moment has come back around; read now)"
                if is_next and s["kairos"]["looping"] else "")
        print(f"  {s['name']:<10} {kind:<9} [{' '.join(parts)}]{marker}{loop}")
        if kind == "UNWRITTEN" and s["forbidden_masks"]:
            told = " · ".join(_mask_wants(s, m) for m in s["forbidden_masks"])
            print(f"             FORBIDDEN tellings: {told}")
    if story["revivals"]:
        print(f"tellings that died: {', '.join(story['revivals'])}")


# -- commands ----------------------------------------------------------------------
def cmd_new(args) -> None:
    base = None
    if STATE_FILE.exists():
        old = json.loads(STATE_FILE.read_text())
        if _server_alive(old.get("base", "")):
            base = old["base"]
            _call(base, "DELETE", f"/v1/sessions/{old['session_id']}")
    if base is None:
        base = _spawn_server()
    r = _call(base, "POST", "/v1/sessions", {"story": "starpod", "seed": args.seed})
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    STATE_FILE.write_text(json.dumps({"base": base, "session_id": r["session_id"]}))
    print(f"A transmission crackles in. (seed {args.seed})")
    print("The first four chapters are already written. The last three are yours to read")
    print("into being — without ever writing a telling the Guard has forbidden.\n")
    st = _load()
    _render_look(_story(st), r["state"]["meta"]["attention"])


def cmd_look(args) -> None:
    st = _load()
    status = _call(st["base"], "GET", f"/v1/sessions/{st['session_id']}/status")
    att = status["state"]["meta"]["attention"] if status.get("ok") else None
    _render_look(_story(st), att)


def cmd_read(args) -> None:
    st = _load()
    r = _call(st["base"], "POST", f"/v1/sessions/{st['session_id']}/choose",
              {"stage": args.stage, "strand": args.strand})
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    res = r["result"]
    ink = res["inked"][args.strand]
    outcome = {1: "it stands realized (+)", -1: "it reads lost/retold (-)",
               0: "the text still shimmers — nothing inked"}[ink]
    print(f"You read {args.stage}.{args.strand}: {outcome}")
    if res["run_state"] == "corrupted":
        print()
    _render_look(r["story"])


def cmd_wait(args) -> None:
    st = _load()
    r = _call(st["base"], "POST", f"/v1/sessions/{st['session_id']}/wait",
              {"steps": args.steps})
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    print(f"The transmission plays on ({args.steps} beats of static).")
    _render_look(_story(st))


def cmd_tell(args) -> None:
    st = _load()
    r = _call(st["base"], "POST", f"/v1/sessions/{st['session_id']}/narrate",
              {"voice": args.voice})
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    n = r["narration"]
    print(f"[{n['voice']}] {n['text']}")


def cmd_revive(args) -> None:
    st = _load()
    r = _call(st["base"], "POST", f"/v1/sessions/{st['session_id']}/revive")
    if not r.get("ok"):
        raise SystemExit(f"error: {r['error']['message']}")
    res = r["result"]
    print(f"Restored from the last coherent stamp ({res['branch_id']}; "
          f"checksum {res['fork_proof']['replayed'][:12]} verified).")
    print("The dead telling is left behind. Choose differently this time.\n")
    _render_look(r["story"])


def cmd_end(args) -> None:
    if STATE_FILE.exists():
        st = json.loads(STATE_FILE.read_text())
        if _server_alive(st.get("base", "")):
            _call(st["base"], "DELETE", f"/v1/sessions/{st['session_id']}")
        STATE_FILE.unlink()
    print("The transmission fades.")


def main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="play", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("--seed", type=int, default=7); p.set_defaults(fn=cmd_new)
    p = sub.add_parser("look"); p.set_defaults(fn=cmd_look)
    p = sub.add_parser("read"); p.add_argument("stage"); p.add_argument("strand"); p.set_defaults(fn=cmd_read)
    p = sub.add_parser("wait"); p.add_argument("steps", type=int, nargs="?", default=12); p.set_defaults(fn=cmd_wait)
    p = sub.add_parser("tell"); p.add_argument("voice", nargs="?", default="rasi"); p.set_defaults(fn=cmd_tell)
    p = sub.add_parser("revive"); p.set_defaults(fn=cmd_revive)
    p = sub.add_parser("end"); p.set_defaults(fn=cmd_end)
    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
