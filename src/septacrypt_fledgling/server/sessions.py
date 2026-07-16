"""SessionStore: session_id → (GameSession, lock).

GameSession is not thread-safe and every verb mutates world/ledger state,
so all access to one session must run under its lock. ThreadingHTTPServer
gives us one thread per request; the store serializes per session while
letting distinct sessions run concurrently.
"""
from __future__ import annotations

import secrets
import threading
from typing import Any, Callable, Dict

from septacrypt_core.api.session import GameSession

from .errors import ApiError

_ALLOWED_CREATE_KEYS = {
    "mode",
    "seed",
    "enable_ledger",
    "private_observers",
    "attention_budget",
    "apply_bridges",
    "include_ground_debug",
}


class SessionStore:
    def __init__(self, max_sessions: int = 64):
        self._lock = threading.Lock()
        self._sessions: Dict[str, GameSession] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self.max_sessions = max_sessions

    def create(self, params: Dict[str, Any]) -> str:
        unknown = set(params) - _ALLOWED_CREATE_KEYS
        if unknown:
            raise ApiError(400, "BadRequest", f"unknown session params: {sorted(unknown)}")
        game = GameSession(**params)
        session_id = secrets.token_hex(8)
        with self._lock:
            if len(self._sessions) >= self.max_sessions:
                raise ApiError(429, "TooManySessions", f"limit {self.max_sessions} reached")
            self._sessions[session_id] = game
            self._locks[session_id] = threading.Lock()
        return session_id

    def delete(self, session_id: str) -> None:
        with self._lock:
            if session_id not in self._sessions:
                raise ApiError(404, "UnknownSession", session_id)
            del self._sessions[session_id]
            del self._locks[session_id]

    def with_session(self, session_id: str, fn: Callable[[GameSession], Any]) -> Any:
        with self._lock:
            game = self._sessions.get(session_id)
            lock = self._locks.get(session_id)
        if game is None or lock is None:
            raise ApiError(404, "UnknownSession", session_id)
        with lock:
            return fn(game)
