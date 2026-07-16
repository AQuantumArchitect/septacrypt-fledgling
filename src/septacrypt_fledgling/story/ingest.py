"""Manuscript ingest: the archived Star Pod index.html -> PassageSpec rows.

The manuscript is already machine-readable: every voice is wrapped in a
`data-layer` span (foreword/guard/translator/seer/myth/outline/appendix),
chapter headings are <h2>, provenance markers are [R#S#] text, and unwritten
sections are `outline` ([[...]]) spans. This parser reads ONLY the archived
canonical file — never the deprecated .docx.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .spec import PassageSpec

MANUSCRIPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs" / "source_artifacts" / "RasiR4S1" / "index.html"
)

STAGE_NAMES = ("Egg", "Gestation", "Birth", "Orbit", "Aegis", "Shepherd", "Cleave")
FRONTMATTER = "_frontmatter"   # foreword + INWORD (Guard/Translator/Seer preambles)
BACKMATTER = "_backmatter"     # Outword + Appendix

_RS = re.compile(r"\[R(\d)S(\d)\]")


@dataclass
class IngestResult:
    passages: List[PassageSpec]
    layer_census: Dict[str, int]  # every data-layer occurrence, incl. nested

    def stage_passages(self, stage: str) -> List[PassageSpec]:
        return [p for p in self.passages if p.stage == stage]


class _ManuscriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_skip = 0            # script/style depth
        self.heading: Optional[str] = None
        self.heading_buf: List[str] = []
        self.stage: str = FRONTMATTER
        self.section_rs: Tuple[int, int] = (0, 0)  # from the latest heading
        self.layer_stack: List[Optional[str]] = []
        self.census: Dict[str, int] = {}
        self.rows: List[dict] = []
        self.current: Optional[dict] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style"):
            self.in_skip += 1
        a = dict(attrs)
        layer = a.get("data-layer")
        if layer:
            self.census[layer] = self.census.get(layer, 0) + 1
        self.layer_stack.append(layer)
        if layer and self.current is None and self.heading is None:
            self.current = {
                "voice": layer,
                "stage": self.stage,
                "section_rs": self.section_rs,
                "text": [],
                "nested_guard": False,
                "depth": len(self.layer_stack),
            }
        elif layer == "guard" and self.current is not None and self.current["voice"] != "guard":
            self.current["nested_guard"] = True
        if tag in ("h1", "h2", "h3", "h4"):
            self._finalize()
            self.heading = tag
            self.heading_buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.in_skip:
            self.in_skip -= 1
        if self.layer_stack:
            self.layer_stack.pop()
        if self.current is not None and len(self.layer_stack) < self.current["depth"]:
            self._finalize()
        if tag in ("h1", "h2", "h3", "h4") and self.heading == tag:
            self._close_heading(tag)

    def handle_data(self, data: str) -> None:
        if self.in_skip:
            return
        if self.heading is not None:
            self.heading_buf.append(data)
            return
        if self.current is not None:
            self.current["text"].append(data)

    def _close_heading(self, tag: str) -> None:
        raw = "".join(self.heading_buf)
        rs = _rs_levels(raw)
        if rs != (0, 0):
            self.section_rs = rs  # passages inherit their section's provenance
        text = _RS.sub("", raw).strip()
        self.heading = None
        if tag != "h2":
            return
        for name in STAGE_NAMES:
            if text.startswith(name):
                self.stage = name
                return
        if text.startswith(("Outword", "Appendix")):
            self.stage = BACKMATTER

    def _finalize(self) -> None:
        if self.current is None:
            return
        text = " ".join("".join(self.current["text"]).split())
        if text:
            self.rows.append({**self.current, "text": text})
        self.current = None

    def close(self) -> None:  # noqa: D102 — flush trailing passage
        self._finalize()
        super().close()


def _rs_levels(text: str) -> Tuple[int, int]:
    removal, speculation = 0, 0
    for r, s in _RS.findall(text):
        removal = max(removal, int(r))
        speculation = max(speculation, int(s))
    return removal, speculation


def ingest_manuscript(path: Path = MANUSCRIPT_PATH) -> IngestResult:
    parser = _ManuscriptParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()

    # Guard excisions over the myth are SIBLING spans, not nested: a top-level
    # guard "[...]" patch interrupts the myth passage before it. Mark that
    # passage corrupted — it is the text the Guard cut into.
    for i, row in enumerate(parser.rows):
        if (
            i > 0
            and row["voice"] == "guard"
            and row["text"].startswith("[")
            and parser.rows[i - 1]["voice"] == "myth"
            and parser.rows[i - 1]["stage"] == row["stage"]
        ):
            parser.rows[i - 1]["nested_guard"] = True

    passages: List[PassageSpec] = []
    for i, row in enumerate(parser.rows):
        removal, speculation = _rs_levels(row["text"])
        if (removal, speculation) == (0, 0):
            removal, speculation = row["section_rs"]
        voice = row["voice"]
        passages.append(
            PassageSpec(
                passage_id=f"p{i:04d}",
                stage=row["stage"],
                voice=voice,
                order=i,
                text=row["text"],
                rs_removal=removal,
                rs_speculation=speculation,
                corrupted=row["nested_guard"] or (voice == "guard" and "[" in row["text"]),
                stub=(voice == "outline"),
            )
        )
    return IngestResult(passages=passages, layer_census=parser.census)


def stage_fog(passages: List[PassageSpec]) -> float:
    """fog = how unwritten a stage is: stub ratio dominates, provenance depth
    and corruption density contribute. Clamped to [0, 1]."""
    if not passages:
        return 1.0  # nothing written at all
    n = len(passages)
    stub_ratio = sum(1 for p in passages if p.stub) / n
    rs_mean = sum(p.rs_removal + p.rs_speculation for p in passages) / (6.0 * n)
    corruption_ratio = sum(1 for p in passages if p.corrupted) / n
    fog = 0.8 * stub_ratio + 0.15 * rs_mean + 0.05 * corruption_ratio
    return max(0.0, min(1.0, fog))
