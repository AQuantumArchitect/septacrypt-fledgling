"""Narrator — renders collapsed story physics into the manuscript's voices.

Strictly OUTSIDE the physics: prose is generated (Anthropic API) or
assembled (deterministic offline fallback) from committed state, journaled
by (stamp_id, physics_hash) so replays reuse text verbatim, and never feeds
back into the substrate. The engine is fully functional with this package
absent or offline.
"""
from .journal import NarrationEntry, NarrationJournal
from .narrate import Narrator

__all__ = ["Narrator", "NarrationEntry", "NarrationJournal"]
