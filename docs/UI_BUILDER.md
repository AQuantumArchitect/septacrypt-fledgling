# UI builder quickstart

Ten commands from zero to a rendered, winnable game state. Requires the two
sibling repos checked out next to this one (see `PINS.md` for exact commits).

```bash
# 1. install (once)
python3 -m venv .venv && . .venv/bin/activate
pip install -e ../umwelt -e ../septacrypt-core -e ".[dev]"

# 2. serve
python -m septacrypt_fledgling.cli serve --port 7777 &

# 3. create a ship game (fast path, ground-truth entities for first bring-up)
curl -s -X POST localhost:7777/v1/sessions \
  -d '{"mode":"ship","seed":3,"enable_ledger":false,"private_observers":false}' \
  | tee /tmp/session.json | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_id"])'
SID=$(python3 -c 'import json; print(json.load(open("/tmp/session.json"))["session_id"])')

# 4. look at the reactor valve
curl -s -X POST localhost:7777/v1/sessions/$SID/look \
  -d '{"observer_id":"me","target_role":"core_valve","zone":"Reactor_Core"}' | python3 -m json.tool | head -40

# 5. let the world breathe
curl -s -X POST localhost:7777/v1/sessions/$SID/wait -d '{"steps":2}' > /dev/null

# 6. check quests
curl -s localhost:7777/v1/sessions/$SID/quests | python3 -m json.tool

# 7. full render payload (this is what you draw)
curl -s "localhost:7777/v1/sessions/$SID/status?observer=me&zone=Reactor_Core" | python3 -m json.tool | head -60

# 8. the machine-readable schema doc
curl -s localhost:7777/v1/schema | python3 -c 'import json,sys; print(json.load(sys.stdin)["render_state_doc"])'
```

What to draw, minimally:

- One card per entry in `state.entities`: `z_axis` (−1…+1) picks the pole
  emoji/pose, `radius` (0…1) is how *certain* the world is (low radius = foggy),
  `semantic.inferred_state` is a ready-made label.
- `state.meta.current_mythos` — emoji + name for the zone's overall vibe.
- `state.meta.attention` — the player's LOOK budget.
- `state.narrative_log` — scrolling story ticker.
- Quest bar from `GET .../quests`; celebrate on `victory: true`.

Seed 3 with the "always LOOK at the lowest-radius role in the active quest
zone, STIR when everything is pinned" policy wins in ~16 turns — good for a
demo reel. `proofs/prove_http_loop.py` plays exactly that game if you want to
watch the HTTP traffic.

When the basic loop renders, switch to the real game feel:
`{"private_observers": true}` — now `entities` is what the *observer believes*,
LOOKs actually reveal things, and fog is real. That's the Fledgling.
