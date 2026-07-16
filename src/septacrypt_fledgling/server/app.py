"""Stdlib HTTP front. ThreadingHTTPServer + a hand-rolled path dispatcher.

URL map (fledgeling.api.v1 — frozen at Arc 1 exit; additive changes only):

  POST   /v1/sessions                      create (mode/seed/... in JSON body)
  DELETE /v1/sessions/{id}                 end session
  GET    /v1/sessions/{id}/status          render.v2 payload (observer/zone/full_ship query)
  POST   /v1/sessions/{id}/wait            {dt_scale?, steps?, zone?, observer_id?}
  POST   /v1/sessions/{id}/look            {observer_id?, target_role, zone?, strength?}
  POST   /v1/sessions/{id}/stir            {observer_id?}
  POST   /v1/sessions/{id}/report          {source, target, role, zone?, confidence?, channel?}
  POST   /v1/sessions/{id}/weave           {start_mask, end_mask}
  GET    /v1/sessions/{id}/quests
  GET    /v1/sessions/{id}/history         (?branch=)
  GET    /v1/schema

Story endpoints (additive post-freeze; 404 on non-story sessions; create a
story session with POST /v1/sessions {"story": "starpod", "seed": N}):

  GET    /v1/sessions/{id}/story           story graph, ink, beats, coherence
  POST   /v1/sessions/{id}/choose          {stage, strand, strength?, observer_id?}
  GET    /v1/sessions/{id}/branches        revival lineage
  POST   /v1/sessions/{id}/revive          fork from the last coherent stamp
  POST   /v1/sessions/{id}/narrate         {voice?} — render latest state as prose
  GET    /v1/sessions/{id}/narration       (?since=stamp_id) — narration journal
"""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qsl, urlparse

from ..schema.envelope import error_envelope
from .errors import ApiError, map_exception
from .routes import Router
from .sessions import SessionStore

_SESSION_PATH = re.compile(r"^/v1/sessions/([0-9a-f]+)(?:/([a-z_]+))?$")

_POST_VERBS = {"wait", "look", "stir", "report", "weave", "choose", "revive", "narrate"}
_GET_VERBS = {"status", "quests", "history", "story", "branches", "narration"}


class _Handler(BaseHTTPRequestHandler):
    router: Router  # set by make_server
    quiet: bool = True

    # -- plumbing ----------------------------------------------------------
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: N802
        if not self.quiet:
            super().log_message(fmt, *args)

    def _send(self, status: int, body: Dict[str, Any]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiError(400, "BadJSON", str(exc)) from exc
        if not isinstance(body, dict):
            raise ApiError(400, "BadJSON", "request body must be a JSON object")
        return body

    def _dispatch(self, method: str) -> Tuple[int, Dict[str, Any]]:
        parsed = urlparse(self.path)
        query = dict(parse_qsl(parsed.query))
        path = parsed.path.rstrip("/") or "/"

        if method == "GET" and path == "/v1/schema":
            return 200, self.router.schema()
        if path == "/v1/sessions":
            if method == "POST":
                return 200, self.router.create_session(self._read_body())
            raise ApiError(405, "MethodNotAllowed", f"{method} {path}")

        m = _SESSION_PATH.match(path)
        if not m:
            raise ApiError(404, "NotFound", path)
        session_id, verb = m.group(1), m.group(2)

        if verb is None:
            if method == "DELETE":
                return 200, self.router.delete_session(session_id)
            raise ApiError(405, "MethodNotAllowed", f"{method} {path}")

        if method == "POST" and verb in _POST_VERBS:
            body = self._read_body()
            return 200, getattr(self.router, verb)(session_id, body)
        if method == "GET" and verb in _GET_VERBS:
            if verb == "quests":
                return 200, self.router.quests(session_id)
            return 200, getattr(self.router, verb)(session_id, query)
        raise ApiError(
            405 if verb in (_POST_VERBS | _GET_VERBS) else 404,
            "MethodNotAllowed" if verb in (_POST_VERBS | _GET_VERBS) else "NotFound",
            f"{method} {path}",
        )

    def _handle(self, method: str) -> None:
        try:
            status, body = self._dispatch(method)
        except Exception as exc:  # noqa: BLE001 — single boundary, mapped explicitly
            status, kind, message = map_exception(exc)
            body = error_envelope(kind, message)
        self._send(status, body)

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle("DELETE")


def make_server(
    host: str = "127.0.0.1",
    port: int = 7777,
    *,
    debug: bool = False,
    max_sessions: int = 64,
    quiet: bool = True,
) -> ThreadingHTTPServer:
    store = SessionStore(max_sessions=max_sessions)
    router = Router(store, debug=debug)
    handler = type("Handler", (_Handler,), {"router": router, "quiet": quiet})
    return ThreadingHTTPServer((host, port), handler)


def serve(host: str = "127.0.0.1", port: int = 7777, *, debug: bool = False) -> None:
    server = make_server(host, port, debug=debug, quiet=False)
    print(f"septacrypt-fledgling serving fledgeling.api.v1 on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


__all__ = ["make_server", "serve"]
