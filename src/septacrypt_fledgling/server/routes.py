"""Endpoint → GameSession verb table.

Every route returns a plain dict (the envelope). Verb payloads are passed
through from septacrypt-core untouched; `status` responses carry the
fledgeling.render.v2 payload under "state".
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from septacrypt_core.api.schema import RENDER_SCHEMA_VERSION, RENDER_STATE_DOC, validate_render_state
from septacrypt_core.api.session import GameSession

from .. import API_VERSION
from ..schema.envelope import error_envelope, ok_envelope
from .errors import ApiError
from .sessions import SessionStore


def _opt_float(body: Dict[str, Any], key: str) -> Optional[float]:
    v = body.get(key)
    return None if v is None else float(v)


class Router:
    def __init__(self, store: SessionStore, *, debug: bool = False):
        self.store = store
        self.debug = debug

    # -- session lifecycle ------------------------------------------------
    def create_session(self, body: Dict[str, Any]) -> Dict[str, Any]:
        session_id = self.store.create(body)
        state = self.store.with_session(session_id, lambda g: self._status(g, {}))
        return ok_envelope(session_id=session_id, state=state)

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        self.store.delete(session_id)
        return ok_envelope(deleted=session_id)

    # -- verbs -------------------------------------------------------------
    def status(self, session_id: str, query: Dict[str, Any]) -> Dict[str, Any]:
        state = self.store.with_session(session_id, lambda g: self._status(g, query))
        return ok_envelope(state=state)

    def wait(self, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        def run(g: GameSession) -> Dict[str, Any]:
            result = g.wait(
                _opt_float(body, "dt_scale"),
                steps=int(body.get("steps", 1)),
                zone=body.get("zone"),
                observer_id=body.get("observer_id", "system"),
            )
            return {"result": result, "state": self._status(g, body)}

        return ok_envelope(**self.store.with_session(session_id, run))

    def look(self, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if "target_role" not in body:
            raise ApiError(400, "BadRequest", "look requires target_role")

        def run(g: GameSession) -> Dict[str, Any]:
            result = g.look(
                body.get("observer_id", "player"),
                body["target_role"],
                zone=body.get("zone"),
                strength=float(body.get("strength", 1.0)),
            )
            return {"result": result, "state": self._status(g, body)}

        return ok_envelope(**self.store.with_session(session_id, run))

    def stir(self, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        def run(g: GameSession) -> Dict[str, Any]:
            result = g.stir(observer_id=body.get("observer_id", "system"))
            return {"result": result, "state": self._status(g, body)}

        return ok_envelope(**self.store.with_session(session_id, run))

    def report(self, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        for key in ("source", "target", "role"):
            if key not in body:
                raise ApiError(400, "BadRequest", f"report requires {key}")

        def run(g: GameSession) -> Dict[str, Any]:
            result = g.report(
                body["source"],
                body["target"],
                body["role"],
                zone=body.get("zone"),
                confidence=float(body.get("confidence", 0.35)),
                channel=body.get("channel", "heard_report"),
            )
            return {"result": result}

        return ok_envelope(**self.store.with_session(session_id, run))

    def weave(self, session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        for key in ("start_mask", "end_mask"):
            if key not in body:
                raise ApiError(400, "BadRequest", f"weave requires {key}")

        def run(g: GameSession) -> Dict[str, Any]:
            return {"story": g.weave(int(body["start_mask"]), int(body["end_mask"]))}

        return ok_envelope(**self.store.with_session(session_id, run))

    def quests(self, session_id: str) -> Dict[str, Any]:
        def run(g: GameSession) -> Dict[str, Any]:
            return {"quests": g.quest_status(), "victory": g.victory()}

        return ok_envelope(**self.store.with_session(session_id, run))

    def history(self, session_id: str, query: Dict[str, Any]) -> Dict[str, Any]:
        def run(g: GameSession) -> Dict[str, Any]:
            return {
                "history": g.history(branch=query.get("branch")),
                "physics_hash": g.physics_hash(),
            }

        return ok_envelope(**self.store.with_session(session_id, run))

    def schema(self) -> Dict[str, Any]:
        return ok_envelope(
            api=API_VERSION,
            render_schema_version=RENDER_SCHEMA_VERSION,
            render_state_doc=RENDER_STATE_DOC,
        )

    # -- helpers -----------------------------------------------------------
    def _status(self, g: GameSession, params: Dict[str, Any]) -> Dict[str, Any]:
        state = g.status(
            params.get("observer_id", params.get("observer", "player")),
            zone=params.get("zone"),
            full_ship=_as_bool(params.get("full_ship", False)),
        )
        if self.debug:
            problems = validate_render_state(state)
            if problems:
                raise ApiError(500, "SchemaDrift", "; ".join(problems))
        return state


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes")


__all__ = ["Router", "error_envelope"]
