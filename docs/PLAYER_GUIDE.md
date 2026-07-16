# STAR POD — how to play

You are the reader of a recovered, partly corrupted transmission: a
seven-chapter book. The first four chapters (Egg, Gestation, Birth, Orbit)
are already written. The last three (Aegis, Shepherd, Cleave) exist only as
shimmering possibility — **you write them by reading them.**

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
python -m septacrypt_fledgling play read STAGE STRAND read one strand (the dice of the book)
python -m septacrypt_fledgling play wait [STEPS]      let the story drift (default 12)
python -m septacrypt_fledgling play tell [VOICE]      hear the narrator (rasi, guard, seer, translator, paul)
python -m septacrypt_fledgling play revive            after corruption: restore and retry
python -m septacrypt_fledgling play end               end the game
```

Stage and strand names are exactly as shown by `play look`
(e.g. `play read Aegis containment`).

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
  `↑` a read will very likely come out `+`, `↓` very likely `-`, `~` a true
  toss-up. **The lean is your dice preview.** It drifts in a slow circle
  (a full loop takes roughly 36 drift-steps), so:
  - want a `+`? read while the arrow is `↑`.
  - want a `-` but the arrow says `↑`? `play wait 12` once or twice until
    the arrow turns, THEN read. Never grind reads against the arrow.

`attention` is your reading budget (each read costs 1; you start with 100).

If the board says a chapter is **going in circles**, its shimmer has come
back to where it was without any story progress — stop waiting and read.

## Staying safe

Before reading a strand, check the lean against the FORBIDDEN list: if the
outcome the arrow points to would complete a forbidden telling with the ink
you already have, fix the other strands first (or wait for the arrow to
turn). Losing always takes two careless readings — the board gives you
everything you need to see the first one coming.

## The texture

`play tell` narrates the latest development in one of the manuscript's five
voices. It never changes the story — but it is the story.
