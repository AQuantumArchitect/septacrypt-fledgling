"""fledgeling.api.v1 envelope.

Every HTTP response body is one of these two shapes. The `state` /
`result` contents inside an ok envelope are septacrypt-core's own
payloads (render schema fledgeling.render.v2 for status; the verb's
native dict otherwise) — the host repo wraps, never rewrites, them.
"""
from __future__ import annotations

from typing import Any, Dict

from .. import API_VERSION


def ok_envelope(**fields: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {"ok": True, "api": API_VERSION}
    body.update(fields)
    return body


def error_envelope(kind: str, message: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "api": API_VERSION,
        "error": {"kind": kind, "message": message},
    }
