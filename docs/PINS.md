# Dependency pins (sprint)

The host repo runs against sibling checkouts installed editable. These are the
exact commits the sprint's gates were verified against; update this file in the
same change as any re-pin.

| Dependency | Commit | Verified by |
|---|---|---|
| umwelt | `5e6d10c` (main, post PR #9 merge — sprint feedback docs+test) | CI green (3.10, 3.12); host suite green against it |
| septacrypt-core | `55166eb` (master, post-sprint: fast path, STIR cap, WorldSpec, Knot* renames) | 28 tests + `proofs/run_all.py` green |

## Install (fresh machine)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ../umwelt -e ../septacrypt-core -e ".[dev]"
python -m pytest -q            # host contract tests
python proofs/prove_http_loop.py
```

Runtime is stdlib-only: the server needs nothing beyond the two engine repos
(numpy comes in transitively).
