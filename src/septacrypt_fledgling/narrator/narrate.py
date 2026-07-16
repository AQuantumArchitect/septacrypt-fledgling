"""Narrator — ties client, voices, fallback and journal to a StorySession.

Pull-based: nothing narrates until asked (POST /narrate or Narrator.narrate).
Mode comes from NARRATOR_MODE (offline | api, default offline); api-mode
failures degrade to the deterministic offline text, so the engine never
depends on the network."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .client import NarratorClient
from .fallback import narrate_offline
from .journal import NarrationEntry, NarrationJournal
from .voices import system_prompt

_PROMPT_ANCHORS = 2
_PROMPT_ANCHOR_CHARS = 400
_PROMPT_RECENT = 3


class Narrator:
    def __init__(
        self,
        mode: Optional[str] = None,
        client: Optional[NarratorClient] = None,
    ):
        self.mode = mode or os.environ.get("NARRATOR_MODE", "offline")
        self.client = client or (NarratorClient() if self.mode == "api" else None)
        self.journal = NarrationJournal()

    # -- public ----------------------------------------------------------------
    def narrate(self, session: Any, voice: str = "rasi") -> NarrationEntry:
        """Narrate the latest committed state of a StorySession."""
        stamp_id = session.ledger.branches.get("main", "genesis")
        physics_hash = session.physics_hash()
        stage_name, verb, strand = self._latest_event(session)
        inked = session.verifier.inked_strands(stage_name)

        def generate() -> Tuple[str, str]:
            if self.client is not None:
                text = self.client.generate(
                    system_prompt(voice),
                    self._prompt(session, voice, stage_name, verb, strand, inked),
                )
                if text:
                    return text, "api"
            return (
                narrate_offline(session.story, stage_name, inked, voice, verb, strand),
                "fallback",
            )

        return self.journal.get_or_create(stamp_id, physics_hash, voice, generate)

    # -- internals ---------------------------------------------------------------
    @staticmethod
    def _latest_event(session: Any) -> Tuple[str, str, Optional[str]]:
        for entry in reversed(session.journal):
            verb, kwargs = entry["verb"], entry["kwargs"]
            if verb == "choose":
                return kwargs["stage"], verb, kwargs["strand"]
            if verb == "look":
                zone = kwargs.get("zone")
                if zone in session.verifier.stages:
                    return zone, "choose", kwargs["target_role"]
            if verb in ("wait", "stir"):
                nxt = session.verifier.next_waypoint()
                stage = nxt[1] if nxt else session.story.stages[-1].name
                return stage, verb, None
        nxt = session.verifier.next_waypoint()
        return (nxt[1] if nxt else session.story.stages[0].name), "wait", None

    def _prompt(
        self,
        session: Any,
        voice: str,
        stage_name: str,
        verb: str,
        strand: Optional[str],
        inked: Dict[str, int],
    ) -> str:
        story = session.story
        stage = story.stage(stage_name)
        st = session.story_state()
        lines: List[str] = [
            f"STAGE: {stage_name} (era {stage.era}, fog {stage.fog:.2f})",
            f"RUN: {st['run_state']}; beats {st['beats']['cursor']}/{st['beats']['total_waypoints']}"
            f" complete: {', '.join(st['beats']['completed'][-3:]) or 'none'}",
        ]
        if verb == "choose" and strand is not None:
            ink = inked.get(strand, 0)
            state = {1: "stands realized", -1: "is lost/retold", 0: "stays unwritten"}[
                1 if ink > 0 else (-1 if ink < 0 else 0)]
            lines.append(f"LATEST READING: the reader read strand '{strand}' — it {state}.")
        else:
            lines.append("LATEST: the transmission played on (no new reading).")
        lines.append(
            "THE TELLING SO FAR IN THIS STAGE: "
            + "; ".join(
                f"{name}: {'realized' if v > 0 else ('lost' if v < 0 else 'unwritten')}"
                for name, v in inked.items()
            )
        )
        anchors = [
            p.text[:_PROMPT_ANCHOR_CHARS]
            for p in stage.passages
            if p.voice in ("myth", voice) and not p.stub
        ][:_PROMPT_ANCHORS]
        for a in anchors:
            lines.append(f"CANONICAL ANCHOR: {a}")
        recent = [e.text for e in self.journal.entries[-_PROMPT_RECENT:]]
        for r in recent:
            lines.append(f"RECENT NARRATION: {r[:200]}")
        if st["corruption"]:
            lines.append(f"CORRUPTION: {st['corruption']['reason']}")
        lines.append("Narrate this development in your voice (<=150 words).")
        return "\n".join(lines)
