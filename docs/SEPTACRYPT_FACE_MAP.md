# SEPTACRYPT_FACE_MAP — the seven faces, as running code

The physical SeptaCrypt (see `source_artifacts/peripheralarbor_septacrypt/`)
has three primary encoded faces, three tertiary faces, and a bottom key face.
FLEDGELING_SEPTACRYPT_PLAN.md §2 maps the architecture onto that object; this
file tracks how much of each face and edge actually runs today.
Typed contracts: `src/septacrypt_fledgling/contracts.py`, conformance gated by
`tests/test_face_contracts.py`.

## Faces

| # | Face | Component | Shipped as | Status |
|---|------|-----------|-----------|--------|
| 1 | Structure (primary) | Universal Architect | `septacrypt_core.architect.ArchitectCompiler` (+ archived `source_artifacts/Universal-Architect@57e3a9a`) | **Skeleton** — compiles CompositeNode trees to EntityRefs; resource-closure logic is a placeholder |
| 2 | Dynamics (primary) | SpaceWheat manifold | `umwelt.substrate.CumulantCluster` as stand-in (real SpaceWheat is Godot-side, already umwelt-compatible via its Witness layer) | **Running (stand-in)** |
| 3 | Belief (primary) | umwelt | `umwelt.host.GameHost` / `WorldSession`; septacrypt's `ObserverBeliefStore` as the lightweight in-kernel variant | **Running** — M2.4 parity holds between the two |
| 4 | Kairos (tertiary) | Berry Tape | `septacrypt_core.geometry.berry.BerryJourney` over umwelt `BerryTape`; coordinates ride every `KnotStamp` | **Running** |
| 5 | History (tertiary) | Knot Ledger | `septacrypt_core.ledger` (KnotStamp/Cassette/TransitionCertificate/KnotLedger) + `world.CertifiedTransaction` | **Running, hardened** (fail-closed replay verification) |
| 6 | Agency (tertiary) | Fledgeling | `GameSession` verbs served by **this repo's** HTTP host (`fledgeling.api.v1`) | **Running** — UI on top is the product work |
| 7 | Meaning (bottom key) | Spirit Cube | `septacrypt_core.spirit.SpiritVector` (7 axes) + `SpiritScorer` | **Declared** — ranking exists; wired into candidate scoring in the Nested Reactor slice |

## Edges (plan §2.2 contracts → implementation)

| Edge | Contract | Today |
|---|---|---|
| Architect → Dynamics | compile components into charts/couplings | **Partial**: `ArchitectCompiler.compile_hierarchy` emits EntityRefs; WorldSpec (M2.1) is the compile target format |
| Dynamics → Belief | publish observations with confidence; never leak ground truth | **Running**: LOOK samples Born outcomes; `private_observers` keeps ground out of the render payload |
| Belief → Architect | request missing probes/topology | Design only |
| Berry Tape → Knot Ledger | kaironic coordinates on durable stamps | **Running**: `berry_coordinate` on every stamp |
| Knot Ledger → Fledgeling | expose history, branches, proofs | **Running**: `GET /v1/sessions/{id}/history` + `physics_hash` |
| Fledgeling → Berry Tape | allocate attention, alter phase through lawful actions | **Running**: attention budget + STIR (typed field cassette) |
| Spirit Cube ↔ all | attach semantic vectors, rank legal options | **Partial**: `SpiritVector.dot` ranking; invariant "spirit reorders, never legalizes" gated in the slice tests |

## Laws that hold across every edge (gated, not aspirational)

1. Physics constrains; spirit ranks legal options; narrative only expresses.
2. No focus-selected physics: a turn advances every zone/mind (pinned in both
   repos' tests, and proposed upstream in umwelt PR #9).
3. Fail-closed history: what cannot be replayed within tolerance is not
   committed; non-finite substrate state never commits.
4. Private minds stay private: an observation lands only in the observer's
   field; reports move targets with less conviction than sight.
