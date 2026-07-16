# septacrypt-fledgling

## ▶ Play STAR POD (fresh machine, five commands)

*Star Sprout / Star Pod* (dudecon/RasiR4S1, public domain) runs here as a
quantum-native story game: the manuscript is the play surface, the unwritten
chapters are live superposition, and you write them by observing them.

```bash
git clone https://github.com/AQuantumArchitect/umwelt
git clone https://github.com/AQuantumArchitect/septacrypt-core
git clone https://github.com/AQuantumArchitect/septacrypt-fledgling
cd septacrypt-fledgling
python3 -m venv .venv && .venv/bin/pip install -e ../umwelt -e ../septacrypt-core -e ".[dev]"
.venv/bin/python -m septacrypt_fledgling play web   # opens the playable manuscript
```

`/play` is the living-document reader (voice toggles intact) with the game
woven in; `/simple` is a plain board. Terminal play: `docs/PLAYER_GUIDE.md`.
How it works: `docs/STORY_PHYSICS.md`. Optional live-LLM narration:
`NARRATOR_MODE=api ANTHROPIC_API_KEY=... ` before `play web`.

---

The **Fledgling host repo** — FL-core Phase 6 of umwelt's
`docs/FLEDGELING_CORE.md` roadmap: the playable product loop that depends on
the engines instead of living inside them.

```text
UI (brother + bots — any language)
   │  JSON over HTTP (fledgeling.api.v1 — docs/API.md)
   ▼
septacrypt-fledgling          this repo: stdlib http server, session store
   │  GameSession verbs
   ▼
septacrypt-core               world/ledger/quest kernel, fail-closed transactions
   │  CumulantCluster / host
   ▼
umwelt                        belief-field substrate (Lindblad cumulant dynamics)
```

- **Quickstart for UI builders:** `docs/UI_BUILDER.md`
- **Frozen HTTP contract:** `docs/API.md`
- **Exact dependency pins + install:** `docs/PINS.md`

Runtime is stdlib-only by design. Gates: `python -m pytest -q` (contract,
name-lint) and `python proofs/prove_http_loop.py` (seed-deterministic full game
to quest victory over HTTP).

Seven-face context: this repo is face 6 (**Fledgeling — agency**) of the
Septacrypt architecture (`umwelt/docs/FLEDGELING_SEPTACRYPT_PLAN.md`);
septacrypt-core carries faces 5 (Knot Ledger) and 7 (Spirit Cube), umwelt
carries face 3 (belief) and the Berry Tape machinery (face 4).
