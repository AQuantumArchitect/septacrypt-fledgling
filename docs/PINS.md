# Dependency pins (sprint)

The host repo runs against sibling checkouts installed editable. These are the
exact commits the sprint's gates were verified against; update this file in the
same change as any re-pin.

| Dependency | Commit | Verified by |
|---|---|---|
| umwelt | `efb0de9` (main, post PR #7 + #8 merge) | `python -m pytest -q` → 231 passed, 2 skipped |
| septacrypt-core | `e7b7262` (master) | 14 tests + `proofs/run_all.py` green |

## Install (fresh machine)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ../umwelt -e ../septacrypt-core -e ".[dev]"
python -m pytest -q            # host contract tests
python proofs/prove_http_loop.py
```

Runtime is stdlib-only: the server needs nothing beyond the two engine repos
(numpy comes in transitively).
