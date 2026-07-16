"""NarrationJournal — prose keyed by (stamp_id, physics_hash), outside the
physics hash by construction. Revival replays regenerate identical stamps,
so their narration is reused verbatim; genuinely new branches miss the cache
and narrate fresh, which is correct — that history is new."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class NarrationEntry:
    stamp_id: str
    physics_hash: str
    voice: str
    text: str
    source: str  # api | fallback | canon


class NarrationJournal:
    def __init__(self) -> None:
        self.entries: List[NarrationEntry] = []
        self._index: Dict[Tuple[str, str, str], NarrationEntry] = {}

    def get(self, stamp_id: str, physics_hash: str, voice: str) -> Optional[NarrationEntry]:
        return self._index.get((stamp_id, physics_hash, voice))

    def get_or_create(
        self,
        stamp_id: str,
        physics_hash: str,
        voice: str,
        generate: Callable[[], Tuple[str, str]],  # -> (text, source)
    ) -> NarrationEntry:
        hit = self.get(stamp_id, physics_hash, voice)
        if hit is not None:
            return hit
        text, source = generate()
        entry = NarrationEntry(
            stamp_id=stamp_id, physics_hash=physics_hash, voice=voice,
            text=text, source=source,
        )
        self.entries.append(entry)
        self._index[(stamp_id, physics_hash, voice)] = entry
        return entry

    def since(self, stamp_id: Optional[str] = None) -> List[NarrationEntry]:
        if stamp_id is None:
            return list(self.entries)
        for i, e in enumerate(self.entries):
            if e.stamp_id == stamp_id:
                return self.entries[i + 1:]
        return list(self.entries)
