"""Exception → (HTTP status, error kind) map.

409 on TransactionError is deliberate API surface: the world refused the
move and is UNCHANGED (fail-closed rollback). Clients should treat 409 as
"retry or change the move", never as corruption.
"""
from __future__ import annotations

from typing import Tuple

from septacrypt_core.world.transaction import TransactionError


class ApiError(Exception):
    """Host-level request error (bad route, unknown session, bad JSON)."""

    def __init__(self, status: int, kind: str, message: str):
        super().__init__(message)
        self.status = status
        self.kind = kind


def map_exception(exc: Exception) -> Tuple[int, str, str]:
    if isinstance(exc, ApiError):
        return exc.status, exc.kind, str(exc)
    if isinstance(exc, TransactionError):
        return 409, "TransactionError", f"{exc} (world unchanged — fail-closed rollback)"
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return 400, type(exc).__name__, str(exc)
    return 500, type(exc).__name__, str(exc)
