"""Anthropic Messages API over stdlib urllib (the host repo is stdlib-only
by law — no SDK). The transport is injectable so tests never touch the
network; any failure returns None and the caller falls back to offline
narration."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"
MAX_TOKENS = 1024
TIMEOUT_S = 30
RETRIES = 2

Transport = Callable[[Dict[str, Any]], Dict[str, Any]]


def _urllib_transport(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read())


class NarratorClient:
    def __init__(self, transport: Optional[Transport] = None, model: Optional[str] = None):
        self.transport = transport or _urllib_transport
        self.model = model or os.environ.get("NARRATOR_MODEL", DEFAULT_MODEL)

    def generate(self, system: str, prompt: str) -> Optional[str]:
        """One narration turn. Returns the text, or None on any failure or
        refusal (the caller falls back to offline narration)."""
        payload = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ],
            "messages": [{"role": "user", "content": prompt}],
        }
        for attempt in range(RETRIES + 1):
            try:
                resp = self.transport(payload)
            except urllib.error.HTTPError as err:
                if err.code in (429, 500, 502, 503, 529) and attempt < RETRIES:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return None
            except Exception:
                return None
            if resp.get("stop_reason") == "refusal":
                return None
            blocks = resp.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            return text.strip() or None
        return None
