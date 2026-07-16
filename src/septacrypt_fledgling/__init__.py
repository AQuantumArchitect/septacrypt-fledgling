"""Fledgling host package: the FL-core Phase 6 integration repo.

This package owns NO engine code. It wraps:
  - septacrypt_core.api.session.GameSession  (world/ledger/quest kernel)
  - umwelt                                    (belief substrate, via septacrypt-core)
behind a stdlib JSON-over-HTTP server so UI builders never import Python.

Name hygiene (ADR-001): this namespace deliberately re-exports none of the
collision-hazard names (GameHost, WorldSession, Observation, Intent) — those
belong to umwelt's belief face. Nor does it re-export GameSession; server code
imports it module-qualified.
"""

__version__ = "0.1.0"

API_VERSION = "fledgeling.api.v1"

__all__ = ["API_VERSION", "__version__"]
