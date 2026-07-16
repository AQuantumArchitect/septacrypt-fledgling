# STORY PHYSICS — Star Pod as a quantum-native story game

The game IS a partially written book. Paul Spooner's *Star Pod* manuscript
(`docs/source_artifacts/RasiR4S1/`, public domain) compiles into a live
quantum world; the player collapses the uncertainty of the unwritten story.
Break the story's continuity and the transmission corrupts — a real loss —
but the ledger lets you fork from the last coherent stamp and retell.

## The pipeline

```
index.html ──story/ingest.py──▶ StorySpec (story/spec.py; lore: story/starpod.py)
        ──story/compile.py──▶ WorldSpec ──GameSession──▶ the live book
StorySession (story/session.py) wraps GameSession:
    ActionJournal + StoryVerifier + revival     narrator/ (prose, outside physics)
    voice minds (umwelt) + spirit + kairos      additive HTTP endpoints
```

## The mapping

| Manuscript | Engine |
|---|---|
| Seven chronological stages (Egg→Cleave) | Seven 3-qubit zones (the text's own triads: Warrior/Wizard/Tinker, Guards/Planters/Seers, human/AI/robot) |
| Written chapters | Boot collapsed at the canonical poles (`init_bloch`), longitudinal fields hold canon, `role_modes="unitary"` makes collapsed text persist |
| Unwritten stubs (Aegis/Shepherd/Cleave) | Deep fog: transverse fields drive genuine superposition — the text shimmers until read |
| The story's causality ("Of the Tinker came the seed of the Gardener…") | Cross-zone bridges: collapsing early chapters biases the fog downstream |
| `[R#S#]` provenance, `[corruption]`, `[[stubs]]` | Per-stage `fog` derived by the ingester |
| Guard-redacted content | `forbidden_masks` — entering one is Mal_Gnosis: instant corruption |
| The beats of the story | `BeatSpec` waypoints, enforced in order by the verifier |
| "Your humanity is your checksum" | `physics_hash` — the fork proof at every revival |

## The laws

1. **Reader-collapse ink.** Text is written only when read. A strand inks
   when a committed reading finds `|z| >= 0.25`; the ink keeps the last
   confident sign while the live state shimmers on. Un-inked strands
   default to canon ("the transmission claims canon until collapsed
   otherwise"). Passive drift, waits and bridges move the live state but
   never write text — corruption only ever flows from the reader's own pen.
2. **Continuity.** After every committed action the StoryVerifier checks:
   no effective mask enters a forbidden state; every mask change has a
   legal Q3 path within the stage's allowed masks; every remaining beat
   waypoint is still reachable. Any failure ⇒ `run_state = corrupted`,
   play verbs refuse (HTTP 409 `TransmissionCorrupted`).
3. **Beats demand written text.** A waypoint is hit only when the stage is
   fully inked AND matches — presumed canon doesn't count until it's read.
4. **Revival is a proven fork.** `revive()` rebuilds the world at the same
   seed and replays the coherent journal prefix; the replayed physics hash
   must equal the recorded one. RNG state at the fork is identical: repeat
   the same fatal choice and it fails the same way — choose differently.
5. **Narration rides outside.** Prose (LLM via `NARRATOR_MODE=api` +
   `ANTHROPIC_API_KEY`, else the deterministic offline fallback) is keyed
   by `(stamp_id, physics_hash)` and never enters the physics. Replays
   reuse text verbatim; new branches narrate fresh.
6. **Spirit ranks, physics gates.** Voice frames reorder the legal next
   masks; they can never legalize a forbidden one (gated).
7. **Kairos hints, never gates.** Berry phase is the chapter's process
   clock; a return without beat progress flags `looping` — a hint only.

## Discovered play mechanics (emergent, not scripted)

- **The shimmer rotation.** In fog, a collapsed pole rotates under the
  transverse drive with period ~37 steps. To rewrite a strand: wait for
  the Semantic Sea to turn, then read again.
- **Quantum Zeno pinning.** Frequent re-reading freezes a strand at its
  pole. Pin what you want to keep; let what you want to flip rotate.
- **Bridge foreshadowing.** Collapsed upstream chapters pump their causal
  successors — Aegis.shield rises because Orbit's Guards stood.

## Playing over HTTP

```bash
python -m septacrypt_fledgling serve --port 7777
curl -X POST localhost:7777/v1/sessions -d '{"story":"starpod","seed":7}'
# then: GET .../story  ·  POST .../choose {"stage":"Aegis","strand":"entity"}
#       POST .../wait {"steps":12}  ·  POST .../narrate {"voice":"rasi"}
#       POST .../revive (after corruption)  ·  GET .../voices  ·  GET .../branches
```

Full narrated playthrough: `python examples/starpod/demo.py --seed 7`.
Gate: `python proofs/prove_story_loop.py` — winnable, losable, revivable,
bit-deterministic.

## Parked (named, deliberate)

- Native `GameSession` branch-play (revival replay covers v1 at zero core risk)
- Core `ArchitectCompiler` emitting WorldSpecs generically (StoryCompiler is
  the host-side StructureFace conformer)
- Per-passage sub-zones (stages are the zone grain), n-role zones (the
  triads fit Q3), complex-topology stages that demand play in response —
  the post-v1 difficulty arc
- Retro/insertion endpoints for story branches; SpaceWheat ground dynamics
  under a stage (the sIMulation war wants it someday)
- Spirit axis naming drift: `SpiritVector.wealth` vs dudecon's
  "Thanksgiving" (`spirit/vector.py:8`) — reconcile when the Spirit Cube
  face gets its own pass
