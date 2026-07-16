# STAR POD — how to play

You are the reader of a recovered, partly corrupted transmission: a
seven-chapter book. The first four chapters (Egg, Gestation, Birth, Orbit)
are already written. The last three (Aegis, Shepherd, Cleave) exist only as
shimmering possibility — **you write them by reading them.**

## Goal

Hit every **beat** of the story, in order. `play look` always shows the next
beat and exactly what it needs — e.g. `in Aegis, the telling must read:
entity+ shield+ containment-`. That means: read each of that chapter's three
strands until `entity` and `shield` stand realized (+) and `containment`
reads lost (-). When every beat is hit, the transmission is complete and you
win.

You LOSE if you write a **forbidden telling** — a combination of strands the
Guard has redacted (Mal_Gnosis). The run corrupts and refuses to continue.
You can always `play revive` to restore the last coherent moment and choose
differently — but the telling you wrote stays dead on a branch.

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

Run these from the repo root. Stage and strand names are exactly as shown by
`play look` (e.g. `play read Aegis containment`).

## How reading works

- Reading a strand asks the book a question; the book answers **+** (stands
  realized) or **-** (lost/retold). In the unwritten chapters the answer is
  genuinely uncertain — you influence which question is asked, not the answer.
- **If a reading comes out the way you don't want:** don't just re-read
  immediately — a fresh answer tends to repeat itself. `play wait 12` first:
  the unwritten text drifts, and the next reading can land the other way.
  Repeat wait-then-read until it inks the way you need.
- What you've read **stays read** (inked) even while the unwritten text keeps
  shimmering underneath. Only your readings change the telling — the drift
  alone never does.
- **Danger:** each reading can flip a strand. Check `play look` before reading
  — if flipping this strand would land the chapter one step from a forbidden
  telling, fix the other strands first. Losing takes two careless readings,
  never one unlucky one.

## Reading the board

```
RUN: coherent | beats 5/9 | attention 93
NEXT BEAT: necrotech-choice — in Shepherd, the telling must read: human+ ai- robot+ ...
  Egg        written   [hacker+ machine+ crowd+]
  Aegis      UNWRITTEN [entity+ shield+ containment-]
  Shepherd   UNWRITTEN [human? ai+ robot?]   <— next beat
```

`+` / `-` = how the strand is inked; `?` = not yet read. Un-read strands
count as the book's default until you read them — but a beat only completes
once you have actually read all three strands of its chapter.

`attention` is your reading budget (each `read` costs 1; you start with 100 —
plenty, but don't grind blindly).

Some beats have two steps (e.g. Aegis first needs `containment-`, then
`containment+`): hit the first telling, then rewrite the strand the other way
(wait-then-read) for the second.

If `play look` says you are going in circles, stop waiting and read something.

## The texture

`play tell` narrates the latest development in one of the manuscript's five
voices. It never changes the story — but it is the story. Use it whenever you
want to know what your readings have done to the book.
