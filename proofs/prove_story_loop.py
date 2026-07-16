"""Story-loop proof: the Star Pod book is winnable, losable, and revivable —
and bit-deterministic.

1. A scripted reader plays Egg -> Cleave to victory (all beats, coherent).
2. A second scripted reader strays into a forbidden telling, loses, revives
   from the last coherent stamp (physics-hash fork proof), and plays on.
3. The same seed + the same choices produce identical physics hashes across
   two independent runs (the narrator, when present, rides OUTSIDE this).

Run: python proofs/prove_story_loop.py
"""
import sys

sys.path.insert(0, "src")

from septacrypt_fledgling.story.session import StorySession, TransmissionCorrupted
from septacrypt_fledgling.story.starpod import STAR_POD

SEED = 7


def ink(s, stage, strand, sign, budget=16):
    for _ in range(budget):
        r = s.choose(stage, strand)
        if s.run_state == "corrupted":
            return False
        if r["inked"][strand] == sign:
            return True
        s.wait(steps=12)
        if s.run_state == "corrupted":
            return False
    return False


WIN_PLAN = (
    ("Aegis", "entity", +1), ("Aegis", "shield", +1),
    ("Aegis", "containment", -1), ("Aegis", "containment", +1),
    ("Shepherd", "human", +1), ("Shepherd", "robot", +1),
    ("Shepherd", "ai", -1), ("Shepherd", "ai", +1),
    ("Cleave", "seed", +1), ("Cleave", "ring", +1), ("Cleave", "earth", -1),
)


def play_to_victory(seed=SEED):
    s = StorySession(STAR_POD, seed=seed)
    s.wait(steps=5)
    for stage, strand, sign in WIN_PLAN:
        assert ink(s, stage, strand, sign), f"could not ink {stage}.{strand} -> {sign}"
    return s


def main() -> None:
    # -- 1. victory ---------------------------------------------------------
    s = play_to_victory()
    st = s.story_state()
    assert st["victory"] and st["run_state"] == "complete", st["run_state"]
    assert st["beats"]["cursor"] == st["beats"]["total_waypoints"] == 9
    win_hash = s.physics_hash()
    print(f"[1] VICTORY  seed={SEED} actions={len(s.journal)} "
          f"attention_left={s.status()['meta']['attention']:.0f} hash={win_hash[:12]}")

    # -- 2. loss + revival ----------------------------------------------------
    s2 = StorySession(STAR_POD, seed=SEED)
    s2.wait(steps=5)
    assert ink(s2, "Shepherd", "ai", +1)
    assert ink(s2, "Shepherd", "human", -1)
    ink(s2, "Shepherd", "robot", -1)  # 010: Mal_Gnosis — this IS the loss
    assert s2.run_state == "corrupted", "straying must corrupt the transmission"
    try:
        s2.wait()
        raise AssertionError("corrupted run accepted a play verb")
    except TransmissionCorrupted:
        pass
    out = s2.revive()
    assert out["fork_proof"]["match"], out
    assert s2.run_state == "coherent"
    assert ink(s2, "Shepherd", "human", +1)  # choose differently this time
    print(f"[2] LOSS+REVIVAL  fork@{out['forked_at_index']} "
          f"proof={out['fork_proof']['replayed'][:12]} corrupted_head="
          f"{out['corrupted_head_hash'][:12]}")

    # -- 3. determinism ---------------------------------------------------------
    s3 = play_to_victory()
    assert s3.physics_hash() == win_hash, "same seed + same choices != same book"
    assert [e["physics_hash"] for e in s3.journal] == [e["physics_hash"] for e in s.journal]
    print(f"[3] DETERMINISM  two full runs, {len(s.journal)} action hashes identical")

    print("\n[PASS] story loop: winnable, losable, revivable, deterministic")


if __name__ == "__main__":
    main()
