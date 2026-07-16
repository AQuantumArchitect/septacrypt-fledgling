# septacrypt-fledgling

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
