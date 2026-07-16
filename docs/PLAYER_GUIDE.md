# STAR POD — how to play

You are the reader of a recovered, partly corrupted transmission: a
seven-chapter book. The first four chapters (Egg, Gestation, Birth, Orbit)
are already written. The last three (Aegis, Shepherd, Cleave) exist only as
shimmering possibility — **you write them by observing them —
and you can always READ the prose your observations have written.**

## Goal

Hit every **beat** of the story, in order. `play look` always shows the next
beat and exactly what it needs — e.g. `in Aegis, the telling must read:
entity+ shield+ containment-`. That means: read that chapter's strands until
`entity` and `shield` stand realized (+) and `containment` reads lost (-).
When every beat is hit, the transmission is complete and you win.

**Beats can have more than one step.** After you hit a beat's telling, the
requirement may change (e.g. Aegis wants `containment-` first, then
`containment+`; Shepherd does the same with `ai`). Don't memorize the steps
— `play look` always shows the CURRENT requirement. Trust the board.

You LOSE if the chapter's inked strands ever form a **FORBIDDEN telling**
(each unwritten chapter's forbidden combinations are listed right on the
board). The run corrupts and refuses to continue. `play revive` restores the
last coherent moment so you can choose differently — it only works after a
corruption, not as a general undo.

## Commands

```
python -m septacrypt_fledgling play new [--seed 7]    start a game
python -m septacrypt_fledgling play look              where the story stands
python -m septacrypt_fledgling play observe STAGE STRAND observe one strand (the dice of the book)
python -m septacrypt_fledgling play wait [STEPS]      let the story drift (default 12)
python -m septacrypt_fledgling play tell [VOICE]      hear the narrator (rasi, guard, seer, translator, paul)
python -m septacrypt_fledgling play revive            after corruption: restore and retry
python -m septacrypt_fledgling play end               end the game
```

Stage and strand names are exactly as shown by `play look`
(e.g. `play observe Aegis containment`). `play web` opens the same game
as a local web page — the full manuscript, playable.

## Reading the board

```
RUN: coherent | beats 5/9 | attention 93
NEXT BEAT: necrotech-choice — in Shepherd, the telling must read: human+ ai- robot+
  Egg        written   [hacker+ machine+ crowd+]
  Aegis      UNWRITTEN [entity+↑ shield+↑ containment-↓]
  Shepherd   UNWRITTEN [human?~ ai+↑ robot?↓]   <— next beat
             FORBIDDEN tellings: human- ai- robot- · human- ai+ robot-
```

Each unwritten strand shows two marks:

- **Ink** — what you have written so far: `+` realized, `-` lost, `?` not yet
  read. Ink only changes when YOU read. Un-read (`?`) strands count as `+`
  for the forbidden-telling check (except Cleave's `earth`, which counts as
  `-`) — but a beat only completes once all three strands of its chapter are
  actually read.
- **Lean** (the arrow) — which way the shimmering text is pointing RIGHT NOW:
  `↑` a read will likely come out `+`, `↓` likely `-`, `~` a true toss-up.
  **The lean predicts; it does not guarantee** — every read is still dice.
  Re-reading a strand is how you REWRITE it: each read re-inks it with the
  fresh answer. The lean drifts in a slow circle (a full loop is roughly 36
  drift-steps), so:
  - want a `+`? read while the arrow is `↑`.
  - want a `-` but the arrow says `↑`? `play wait 12` once or twice until
    the arrow turns, THEN read — don't waste reads fighting the arrow.
  - **Some strands are fed by the story's own causality** (earlier chapters
    push them) and their lean favors one side, rarely turning all the way.
    Flipping one of those is the hardest move in the game: wait for `~` and
    take the coin flip.

`attention` is your reading budget (each read costs 1; you start with 100 —
a clean run takes roughly 15–35 reads, so you have real slack).

If the board says the next-beat chapter is **going in circles**, its shimmer
has come back to where it was without any story progress — stop waiting and
read.

**Leave finished chapters alone.** Their strands keep shimmering, but their
beats are banked. Reading one again is legal — it can also un-write a
telling you needed; if you disturb one, read it back to what its beat
demanded before the end.

## Staying safe

Before reading a strand, check the lean against the FORBIDDEN list: if the
outcome the arrow points to would complete a forbidden telling with the ink
you already have, fix the other strands first (or wait for the arrow to
turn). Losing always takes two careless readings — the board gives you
everything you need to see the first one coming.

## The texture

`play tell` narrates the latest development in one of the manuscript's five
voices. It never changes the story — but it is the story.
