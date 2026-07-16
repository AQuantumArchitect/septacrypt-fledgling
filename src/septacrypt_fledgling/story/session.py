"""StorySession — a GameSession playing a StorySpec, with the continuity law.

Mirrors the GameSession verb surface (so the frozen HTTP routes work
unchanged) and adds the story layer: an ActionJournal (every committed verb
+ the physics hash after it), the StoryVerifier post-commit hook, real loss
("transmission corrupted"), and revival by deterministic rebuild-replay from
the last coherent action — the determinism gate made into a runtime fork
proof.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from septacrypt_core.api.session import GameSession

from .compile import compile_story
from .kairos import KairosTracker, chapter_phase
from .spec import StorySpec, VoiceSpec
from .spirit import SpiritFrames
from .verifier import StoryVerifier, Verdict

_MIND_STEP_CAP = 50  # lazy belief-relaxation catch-up cap per read

PLAY_VERBS = ("wait", "look", "stir", "report", "choose")


class TransmissionCorrupted(Exception):
    """Raised when a play verb is attempted on a corrupted run."""


@dataclass
class BranchRecord:
    branch_id: str
    forked_at_index: int          # journal index of the last coherent action
    forked_at_hash: str           # physics hash at the fork point
    corrupted_head_hash: str      # where the dead telling ended
    corruption_reason: str


class StorySession:
    def __init__(self, story: StorySpec, *, seed: int = 0, debug: bool = False):
        self.story = story
        self.seed = int(seed)
        self.world_spec = compile_story(story)
        self.debug = debug
        self.journal: List[Dict[str, Any]] = []
        self.last_coherent = 0
        self.revivals: List[BranchRecord] = []
        self.completed_beats: List[str] = []
        self.run_state = "coherent"  # coherent | corrupted | complete
        self.corruption: Optional[Verdict] = None
        self._replaying = False
        self.spirit = SpiritFrames(story)
        self._voice_coverage: Dict[Tuple[str, str], List[VoiceSpec]] = {}
        for v in story.voices:
            for stage, strand in v.observes:
                self._voice_coverage.setdefault((stage, strand), []).append(v)
        self._boot()

    # -- lifecycle ------------------------------------------------------------
    def _boot(self) -> None:
        self.game = GameSession(
            spec=self.world_spec,
            seed=self.seed,
            enable_ledger=True,
            private_observers=True,
        )
        self.verifier = StoryVerifier(self.story)
        self.verifier.absorb_boot_ink(self.game)
        boot = self.verifier.check(self.game)
        if boot.coherent:
            self.completed_beats.extend(boot.completed_beats)
        self.kairos = KairosTracker()
        self._minds = None  # built lazily; observations buffer until then
        self._mind_events: List[Tuple[str, str, float, float]] = []
        self._pending_mind_steps = 0

    def revive(self) -> Dict[str, Any]:
        """Fork from the last coherent stamp: rebuild + replay the journal
        prefix, prove the fork by physics-hash equality, resume play."""
        if self.run_state != "corrupted":
            raise ValueError("revive() only applies to a corrupted run")
        dead_hash = self.game.physics_hash()
        reason = self.corruption.reason if self.corruption else ""
        prefix = self.journal[: self.last_coherent]

        self.journal = []
        self.completed_beats = []
        self.run_state = "coherent"
        self.corruption = None
        self._boot()
        self._replaying = True
        try:
            for entry in prefix:
                getattr(self, entry["verb"])(**entry["kwargs"])
        finally:
            self._replaying = False

        replayed_hash = self.game.physics_hash()
        expected = prefix[-1]["physics_hash"] if prefix else self.game.physics_hash()
        if replayed_hash != expected:
            raise AssertionError(
                f"revival replay diverged: {replayed_hash} != recorded {expected}"
            )
        if self.run_state != "coherent":
            raise AssertionError("revival replay re-corrupted a coherent prefix")

        record = BranchRecord(
            branch_id=f"revival-{len(self.revivals) + 1}",
            forked_at_index=len(prefix),
            forked_at_hash=replayed_hash,
            corrupted_head_hash=dead_hash,
            corruption_reason=reason,
        )
        self.revivals.append(record)
        return {
            "branch_id": record.branch_id,
            "forked_at_index": record.forked_at_index,
            "fork_proof": {"replayed": replayed_hash, "recorded": expected, "match": True},
            "corrupted_head_hash": dead_hash,
        }

    # -- the committed-verb pipeline -------------------------------------------
    def _guard(self) -> None:
        if self.run_state == "corrupted":
            reason = self.corruption.reason if self.corruption else "unknown corruption"
            raise TransmissionCorrupted(
                "transmission corrupted — your humanity is your checksum; "
                f"restore from the last coherent stamp (revive). Cause: {reason}"
            )

    def _commit(self, verb: str, kwargs: Dict[str, Any], result: Any,
                touched: Optional[Tuple[str, str]] = None) -> Any:
        self.journal.append(
            {"verb": verb, "kwargs": kwargs, "physics_hash": self.game.physics_hash()}
        )
        verdict = self.verifier.check(self.game, touched=touched)
        self.kairos.observe(self)
        if verb == "wait":
            self._pending_mind_steps += int(kwargs.get("steps") or 1)
        if touched is not None:
            self._witness(touched)
        if verdict.coherent:
            self.last_coherent = len(self.journal)
            self.completed_beats.extend(verdict.completed_beats)
            if self.verifier.beats_complete() and self._quests_met():
                self.run_state = "complete"
        else:
            self.run_state = "corrupted"
            self.corruption = verdict
        return result

    # -- voice minds (umwelt WorldSession; epistemic layer, outside physics) ----
    @property
    def minds(self):
        if self._minds is None:
            from ..minds.adapter import UmweltMindsAdapter

            roles = tuple(
                f"{s.name}_{st.name}" for s in self.story.stages for st in s.strands
            )
            self._minds = UmweltMindsAdapter(roles)
            for v in self.story.voices:
                if v.observes:
                    self._minds.add_observer(v.name)
        return self._minds

    def _witness(self, touched: Tuple[str, str]) -> None:
        """A committed reading lands in the private minds of every voice
        whose coverage includes the read strand — at that voice's efficiency.
        Voices witness the outcome, never the ground state itself."""
        voices = self._voice_coverage.get(touched)
        if not voices:
            return
        stage, strand = touched
        z = float(self.game.world.zones[stage].role_bloch(strand)[2])
        outcome = 1.0 if z >= 0 else -1.0
        for v in voices:
            self.minds.saw(v.name, f"{stage}_{strand}", outcome, confidence=v.efficiency)

    def voices_state(self) -> Dict[str, Any]:
        steps = min(self._pending_mind_steps, _MIND_STEP_CAP)
        if steps and self._minds is not None:
            self._minds.step(steps)
        self._pending_mind_steps = 0
        out: Dict[str, Any] = {}
        for v in self.story.voices:
            if not v.observes:
                continue
            beliefs = self.minds.beliefs_snapshot(v.name)
            covered = {f"{stage}_{strand}" for stage, strand in v.observes}
            out[v.name] = {
                "register": v.register,
                "spirit_frame": list(v.spirit_frame),
                "beliefs": {
                    role: {"z": round(z, 4), "confidence": round(c, 4)}
                    for role, (z, c) in beliefs.items()
                    if role in covered
                },
            }
        return out

    def _quests_met(self) -> bool:
        return all(
            self.verifier.effective_mask(q.zone) == q.target_mask
            for q in self.world_spec.quests
        )

    # -- play verbs (GameSession surface, journaled + verified) ----------------
    def wait(self, dt_scale: Optional[float] = None, *, steps: int = 1,
             zone: Optional[str] = None, observer_id: str = "system") -> Any:
        self._guard()
        result = self.game.wait(dt_scale, steps=steps, zone=zone, observer_id=observer_id)
        return self._commit(
            "wait",
            {"dt_scale": dt_scale, "steps": steps, "zone": zone, "observer_id": observer_id},
            result,
        )

    def look(self, observer_id: str, target_role: str, *,
             zone: Optional[str] = None, strength: float = 1.0) -> Any:
        self._guard()
        result = self.game.look(observer_id, target_role, zone=zone, strength=strength)
        return self._commit(
            "look",
            {"observer_id": observer_id, "target_role": target_role,
             "zone": zone, "strength": strength},
            result,
            touched=(zone or self.game.world.active_zone, target_role),
        )

    def choose(self, stage: str, strand: str, *, strength: float = 1.0,
               observer_id: str = "player") -> Dict[str, Any]:
        """A committed reading: the player chooses which question to ask the
        text; the Born rule answers."""
        self._guard()
        if stage not in self.verifier.stages:
            raise ValueError(f"unknown stage {stage!r}")
        if strand not in self.verifier.stages[stage].strand_names:
            raise ValueError(f"unknown strand {stage}.{strand}")
        result = self.game.look(observer_id, strand, zone=stage, strength=strength)
        self._commit(
            "choose",
            {"stage": stage, "strand": strand, "strength": strength,
             "observer_id": observer_id},
            result,
            touched=(stage, strand),
        )
        return {
            "look": result,
            "inked": self.verifier.inked_strands(stage),
            "effective_mask": self.verifier.effective_mask(stage),
            "run_state": self.run_state,
        }

    def stir(self, observer_id: str = "system") -> Any:
        self._guard()
        result = self.game.stir(observer_id=observer_id)
        return self._commit("stir", {"observer_id": observer_id}, result)

    def report(self, source: str, target: str, role: str, *,
               zone: Optional[str] = None, confidence: float = 0.35,
               channel: str = "heard_report") -> Any:
        self._guard()
        result = self.game.report(
            source, target, role, zone=zone, confidence=confidence, channel=channel
        )
        return self._commit(
            "report",
            {"source": source, "target": target, "role": role, "zone": zone,
             "confidence": confidence, "channel": channel},
            result,
        )

    # -- read-only surface (delegated) ------------------------------------------
    def status(self, observer_id: str = "player", **kwargs: Any) -> Any:
        return self.game.status(observer_id, **kwargs)

    def weave(self, start_mask: int, end_mask: int) -> str:
        return self.game.weave(start_mask, end_mask)

    def quest_status(self) -> Any:
        return self.game.quest_status()

    def victory(self) -> bool:
        return self.run_state == "complete"

    def history(self, branch: Optional[str] = None) -> Any:
        return self.game.history(branch=branch)

    def physics_hash(self) -> str:
        return self.game.physics_hash()

    @property
    def world(self):  # parity with GameSession for read paths
        return self.game.world

    @property
    def ledger(self):
        return self.game.ledger

    # -- narration (pull-based; strictly outside the physics) --------------------
    @property
    def narrator(self):
        if getattr(self, "_narrator", None) is None:
            from ..narrator import Narrator

            self._narrator = Narrator()
        return self._narrator

    def narrate(self, voice: str = "rasi") -> Dict[str, Any]:
        e = self.narrator.narrate(self, voice=voice)
        return {"stamp_id": e.stamp_id, "physics_hash": e.physics_hash,
                "voice": e.voice, "text": e.text, "source": e.source}

    def narration(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {"stamp_id": e.stamp_id, "physics_hash": e.physics_hash,
             "voice": e.voice, "text": e.text, "source": e.source}
            for e in self.narrator.journal.since(since)
        ]

    # -- story read model ---------------------------------------------------------
    def story_state(self) -> Dict[str, Any]:
        nxt = self.verifier.next_waypoint()
        stages = []
        for s in sorted(self.story.stages, key=lambda s: s.order):
            legal = self.verifier.legal_next_masks(s.name)
            cluster = self.game.world.zones[s.name]
            stages.append({
                "name": s.name,
                "era": s.era,
                "fog": s.fog,
                "strands": [st.name for st in s.strands],
                "inked": self.verifier.inked_strands(s.name),
                # which way the live text is leaning right now — the visible
                # shimmer of the page (deliberate, diegetic: reading the lean
                # IS part of reading the book)
                "lean": {
                    st.name: round(float(cluster.role_bloch(st.name)[2]), 3)
                    for st in s.strands
                },
                "effective_mask": self.verifier.effective_mask(s.name),
                "canonical_mask": s.canonical_mask,
                "forbidden_masks": list(s.forbidden_masks),
                "legal_next_masks": legal,
                "spirit_ranked": self.spirit.rank(s.name, legal),
                "kairos": {
                    **chapter_phase(self, s.name),
                    "looping": self.kairos.looping(s.name),
                },
            })
        return {
            "story_id": self.story.story_id,
            "version": self.story.version,
            "run_state": self.run_state,
            "corruption": (
                {"reason": self.corruption.reason, "rule": self.corruption.rule,
                 "stage": self.corruption.stage}
                if self.corruption else None
            ),
            "beats": {
                "completed": list(self.completed_beats),
                "next_waypoint": (
                    {"beat_id": nxt[0], "stage": nxt[1], "mask": nxt[2]} if nxt else None
                ),
                "total_waypoints": len(self.verifier.waypoints),
                "cursor": self.verifier.cursor,
            },
            "stages": stages,
            "journal_length": len(self.journal),
            "last_coherent": self.last_coherent,
            "revivals": [r.branch_id for r in self.revivals],
            "victory": self.victory(),
        }
