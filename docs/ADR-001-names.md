# ADR-001: Vocabulary ownership across the three repos

**Status:** accepted (sprint, 2026-07)

## Problem

umwelt and septacrypt-core independently invented classes named `GameHost`,
`WorldSession`, `Observation`, and `Intent` with structurally incompatible
shapes (flagged in the boot_strap_REPL_merge MANIFEST). Any code importing
both stacks — this host repo by definition — risks silent confusion.

## Decision

| Vocabulary | Owner | Examples |
|---|---|---|
| Belief-face (plain game words) | **umwelt** (`umwelt.host`) | `GameHost`, `WorldSession`, `Observation`, `Intent`, `Belief`, `Decision` |
| Ledger/world (knot words) | **septacrypt-core** | `KnotStamp`, `KnotObservation`, `KnotIntent`, `CertifiedTransaction`, `World`, `GameSession`, `Cassette` |
| — | **septacrypt-fledgling** | owns neither; re-exports neither |

- septacrypt-core renamed its `Observation` → `KnotObservation` and `Intent` →
  `KnotIntent` (ledger/stamp.py) with `DeprecationWarning` aliases for one
  release. It defines no `GameHost`/`WorldSession` of its own — `narrative/
  patrol.py` correctly imports umwelt's.
- The host namespace ships a lint test (`tests/test_name_lint.py`) asserting
  none of the hazard names (nor `GameSession`) leak into
  `septacrypt_fledgling`'s exports; all imports are module-qualified.

## Direction of travel (FIELD_NOTES §4)

Long-term, septacrypt's minds should attach through umwelt's front door
(`GameHost`/`WorldSession`), not hand-built clusters. The M2.4 convergence
probe explores that; this ADR records the naming boundary that makes the
coexistence safe meanwhile.
