# fledgeling.api.v1 — HTTP contract

**FROZEN as of Arc 1 exit.** Additive changes only (new optional fields, new
endpoints); nothing listed here will be renamed, removed, or change shape.

Start the server:

```bash
python -m septacrypt_fledgling.cli serve --port 7777          # production
python -m septacrypt_fledgling.cli serve --port 7777 --debug  # validates every payload
```

All bodies are JSON. Every response is one of:

```json
{ "ok": true,  "api": "fledgeling.api.v1", ... }
{ "ok": false, "api": "fledgeling.api.v1", "error": {"kind": "...", "message": "..."} }
```

## Endpoints

| Method & path | Body / query | Returns |
|---|---|---|
| `POST /v1/sessions` | `{mode, seed, enable_ledger?, private_observers?, attention_budget?, apply_bridges?, include_ground_debug?}` | `{session_id, state}` |
| `DELETE /v1/sessions/{id}` | — | `{deleted}` |
| `GET /v1/sessions/{id}/status` | `?observer=&zone=&full_ship=` | `{state}` |
| `POST /v1/sessions/{id}/wait` | `{dt_scale?, steps?, zone?, observer_id?}` | `{result, state}` |
| `POST /v1/sessions/{id}/look` | `{observer_id?, target_role, zone?, strength?}` | `{result, state}` |
| `POST /v1/sessions/{id}/stir` | `{observer_id?}` | `{result, state}` |
| `POST /v1/sessions/{id}/report` | `{source, target, role, zone?, confidence?, channel?}` | `{result}` |
| `POST /v1/sessions/{id}/weave` | `{start_mask, end_mask}` | `{story}` |
| `GET /v1/sessions/{id}/quests` | — | `{quests: [...], victory: bool}` |
| `GET /v1/sessions/{id}/history` | `?branch=` | `{history: [...], physics_hash}` |
| `GET /v1/schema` | — | `{render_schema_version, render_state_doc}` |

`state` is septacrypt-core's `fledgeling.render.v2` payload verbatim — the
machine-readable field doc is served at `GET /v1/schema`.

## Session parameters that matter for a UI

- `mode`: `"reactor"` (1 zone, 3 roles) or `"ship"` (3 zones + soft bridges + quests).
- `seed`: same seed + same calls ⇒ identical worlds (bit-for-bit; `physics_hash` proves it).
- `enable_ledger`: `true` (default) gives witnessed, certificate-verified history
  (~50 ms/action); `false` uses the fast path (~2 ms/action) with no ledger. For a
  live UI loop, `false` is usually right; turn it on when the game wants provable history.
- `private_observers`: `true` (default) means `entities` shows the observer's
  *beliefs* (fog); ground truth moves only when that observer LOOKs or receives a
  `report`. `false` shows ground truth directly (arcade mode / debugging).
- `attention_budget`: LOOK costs 1.0 of it; `null` for unlimited.

## Error semantics

| Status | Kind | Meaning |
|---|---|---|
| 400 | `BadRequest` / `ValueError` / `BadJSON` | malformed input; fix the call |
| 404 | `UnknownSession` / `NotFound` | bad session id or path |
| 405 | `MethodNotAllowed` | wrong verb on a valid path |
| 409 | `TransactionError` | **the world refused the move and is unchanged** — fail-closed rollback is a feature; retry or change the move |
| 429 | `TooManySessions` | session cap reached (default 64) |
| 500 | `SchemaDrift` / other | server bug — report it |

A 409 can never corrupt state: the engine replays and verifies every certified
transition, and both commit paths roll back completely on failure (including
non-finite physics, which is rejected rather than committed).

## Game loop cheat-sheet

1. `POST /v1/sessions` → keep `session_id`.
2. Render from `state.entities` (per role: `raw_metrics.z_axis` in [-1,1],
   `raw_metrics.radius` = confidence, `semantic.inferred_state`) and
   `state.meta.current_mythos` (emoji + name).
3. Player acts: LOOK (spends attention, collapses a role), WAIT (world evolves,
   bridges couple zones), STIR (transverse kick — escape hatch when everything
   is pinned near poles).
4. Poll `GET .../quests` for `victory`.
5. `state.narrative_log` is the story ticker; `GET .../history` is the witnessed
   knot for timeline UIs.

## Story endpoints (additive, post-freeze)

A **story session** plays a StorySpec — v1 ships `starpod` (Paul Spooner's
*Star Pod*, public domain). Create with `POST /v1/sessions
{"story": "starpod", "seed": 7}`; all frozen v1 verbs work unchanged, plus
(404 `NotAStorySession` on plain sessions):

| Endpoint | Method | Notes |
|---|---|---|
| `.../story` | GET | story graph: stages (fog, inked strands, effective/canonical/forbidden masks, legal next masks, per-voice `spirit_ranked`, `kairos` phase + `looping`), beat cursor, `run_state`, revivals |
| `.../choose` | POST | `{stage, strand, strength?, observer_id?}` — a committed reading; the Born rule answers. Returns ink + verifier verdict |
| `.../revive` | POST | after corruption: fork from the last coherent stamp with a physics-hash fork proof |
| `.../branches` | GET | revival lineage (the tellings that died) |
| `.../narrate` | POST | `{voice?}` (guard/translator/seer/rasi/paul) — render the latest state as prose. Cached by `(stamp_id, physics_hash)` |
| `.../narration` | GET | `?since=stamp_id` — the narration journal |
| `.../voices` | GET | the four voice minds' private beliefs (umwelt WorldSession) |

New error kind: **409 `TransmissionCorrupted`** — the run is lost (a play
verb was attempted on a corrupted story). This differs from
`TransactionError`: the world is fine, the STORY is broken; `POST .../revive`
is the way back. See `docs/STORY_PHYSICS.md` for the laws.
