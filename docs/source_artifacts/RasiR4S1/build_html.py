#!/usr/bin/env python3
"""Build index.html: Star Sprout / Star Pod with toggleable authorial voice layers.

Usage:
  python build_html.py
  python build_html.py path/to/manuscript.docx

Reads the .docx (default: Star Sprout [R4S1].docx) and writes index.html.
"""

from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

DEFAULT_DOCX = Path("Star Sprout [R4S1].docx")
OUT_PATH = Path("index.html")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Layer ids used in CSS/JS
LAYERS = [
    ("foreword", "Foreword", "Paul — metatextual address outside the transmission game"),
    ("guard", "Guard", "Sanitization, checksum warnings, bracketed corruption patches"),
    ("translator", "Translator", "Scholarly notes and parenthetical glosses"),
    ("seer", "Seer", "Liturgical framing and curly-brace omissions"),
    ("myth", "Main myth", "Rasi’s narrative and the people’s origin saga"),
    ("outline", "Structural stubs", "Compressed / unfinished synopsis blocks [[…]]"),
    ("appendix", "Appendix", "Workshop notes, tech eras, structural map"),
]

OPENERS = {"(": "translator", "[": "guard", "{": "seer"}
CLOSERS = {")": "translator", "]": "guard", "}": "seer"}
MATCH = {"(": ")", "[": "]", "{": "}"}


def escape(s: str) -> str:
    return html.escape(s, quote=False)


def is_revision_token(text: str) -> bool:
    """True if entire bracket content looks like a revision tag, e.g. R1S0, R4S1."""
    t = text.strip()
    return bool(re.fullmatch(r"R\d+S\d+", t))


def parse_inline(text: str, default_layer: str | None) -> str:
    """
    Parse nested (translator) [guard] {seer} delimiters into layered spans.
    Plain text is tagged with default_layer so interlinear voices can be
    shown while the host voice is hidden (and vice versa).
    Revision tags [R1S0] stay on the default layer. Double [[stubs]] -> outline.
    """
    if not text:
        return ""

    out: list[str] = []
    stack: list[tuple[str, str]] = []  # (layer, open_char)
    i = 0
    n = len(text)
    buf: list[str] = []

    def flush_buf() -> None:
        """Emit buffered plain text, wrapped in default_layer when at top level."""
        nonlocal buf
        if not buf:
            return
        chunk = "".join(buf)
        buf = []
        if not chunk:
            return
        esc = escape(chunk)
        if default_layer and not stack:
            out.append(
                f'<span class="layer layer-{default_layer}" data-layer="{default_layer}">'
                f"{esc}</span>"
            )
        else:
            # Inside a voice span: text inherits parent layer (no extra wrap)
            out.append(esc)

    def open_span(layer: str, ch: str) -> None:
        flush_buf()
        stack.append((layer, ch))
        out.append(f'<span class="layer layer-{layer}" data-layer="{layer}">')
        out.append(escape(ch))

    def close_span(ch: str) -> bool:
        if not stack:
            return False
        _layer, open_ch = stack[-1]
        if MATCH[open_ch] != ch:
            return False
        flush_buf()
        out.append(escape(ch))
        out.append("</span>")
        stack.pop()
        return True

    while i < n:
        # Double-bracket outline stubs: [[ ... ]]
        if text.startswith("[[", i):
            end = text.find("]]", i + 2)
            if end != -1:
                flush_buf()
                inner = text[i : end + 2]
                out.append(
                    f'<span class="layer layer-outline" data-layer="outline">'
                    f"{escape(inner)}</span>"
                )
                i = end + 2
                continue

        ch = text[i]

        if ch in OPENERS:
            if ch == "[":
                close = text.find("]", i + 1)
                if close != -1:
                    inner = text[i + 1 : close]
                    if is_revision_token(inner):
                        buf.append(text[i : close + 1])
                        i = close + 1
                        continue
            open_span(OPENERS[ch], ch)
            i += 1
            continue

        if ch in CLOSERS:
            if close_span(ch):
                i += 1
                continue
            buf.append(ch)
            i += 1
            continue

        buf.append(ch)
        i += 1

    flush_buf()
    while stack:
        out.append("</span>")
        stack.pop()

    return "".join(out)


def classify_section(style: str, text: str, current: str) -> str:
    """Update section layer from heading text."""
    t = text.strip()
    low = t.lower()

    if style == "Title" or style == "Subtitle":
        return "chrome"  # always visible chrome

    if style.startswith("Heading"):
        if "metatextual" in low or "foreword" in low:
            return "foreword"
        if low == "inword" or low == "outword":
            return "chrome"
        if "guard" in low:
            return "guard"
        if "translator" in low:
            return "translator"
        if "seer" in low:
            return "seer"
        if "appendix" in low or low in (
            "notes",
            "technology",
            "structure",
            "zerotech encounter",
        ):
            # Appendix and its subheads; structure subsections share appendix layer
            if "appendix" in low or low in ("notes", "technology", "structure"):
                return "appendix"
            # Zerotech is under Shepherd in appendix outline
            if current == "appendix":
                return "appendix"
        if any(
            k in low
            for k in (
                "egg",
                "gestation",
                "birth",
                "orbit",
                "aegis",
                "shepherd",
                "cleave",
                "history informs",
                "proto-life",
                "conviction",
                "deck’s garden",
                "deck's garden",
                "golden city",
                "why the aliens",
            )
        ):
            return "myth"
        # Egg/Gestation etc. as appendix subheads when already in appendix
        if current == "appendix" and any(
            k in low
            for k in (
                "egg",
                "gestation",
                "birth",
                "orbit",
                "aegis",
                "shepherd",
                "cleave",
            )
        ):
            return "appendix"

    return current


def heading_level(style: str) -> int | None:
    if style == "Title":
        return 1
    if style == "Subtitle":
        return None
    m = re.match(r"Heading(\d)", style)
    if m:
        return int(m.group(1))
    return None


def build_body(paras: list[dict]) -> str:
    parts: list[str] = []
    section = "chrome"
    in_appendix = False

    for p in paras:
        style = p["style"]
        text = p["text"]
        stripped = text.strip()

        # Detect appendix entry and stay there
        if style.startswith("Heading") and "appendix" in stripped.lower():
            in_appendix = True
            section = "appendix"
        elif in_appendix:
            section = "appendix"
        else:
            section = classify_section(style, text, section)

        # Empty line
        if not stripped:
            parts.append('<p class="spacer" aria-hidden="true"></p>')
            continue

        hl = heading_level(style)
        if style == "Title":
            parts.append(
                f'<header class="doc-header layer layer-chrome" data-layer="chrome">'
                f"<h1>{escape(stripped)}</h1>"
            )
            continue
        if style == "Subtitle":
            # May follow title or section
            if parts and parts[-1].startswith('<header class="doc-header'):
                parts[-1] = (
                    parts[-1]
                    + f'<p class="tagline">{escape(stripped)}</p></header>'
                )
            else:
                default = None if section == "chrome" else section
                inner = parse_inline(stripped, default)
                parts.append(f'<p class="subtitle">{inner}</p>')
            continue

        if hl is not None:
            # Close unclosed header if needed
            if parts and parts[-1].startswith('<header class="doc-header') and not parts[
                -1
            ].endswith("</header>"):
                parts[-1] += "</header>"

            layer = "chrome" if section == "chrome" else section
            if style == "Heading1":
                tag = "h2"
            elif style == "Heading2":
                tag = "h3"
            elif style == "Heading3":
                tag = "h4"
            elif style == "Heading4":
                tag = "h5"
            else:
                tag = "h2"

            default = None if layer == "chrome" else layer
            # Appendix headings are plain workshop labels (no Guard/Translator markup).
            if layer == "appendix":
                heading_html = (
                    f'<span class="layer layer-appendix" data-layer="appendix">'
                    f"{escape(stripped)}</span>"
                )
            else:
                heading_html = parse_inline(stripped, default)
            parts.append(f"<{tag}>{heading_html}</{tag}>")
            continue

        # Body paragraph
        default = None if section == "chrome" else section
        # Workshop appendix uses parentheses as ordinary notes, not Translator voice.
        if section == "appendix":
            inner = (
                f'<span class="layer layer-appendix" data-layer="appendix">'
                f"{escape(text)}</span>"
            )
        else:
            # Guard/translator/seer/myth: parse inline so nested markers work.
            inner = parse_inline(text, default)
        parts.append(f"<p>{inner}</p>")

    # Close header if still open
    if parts and parts[-1].startswith('<header class="doc-header') and not parts[
        -1
    ].endswith("</header>"):
        parts[-1] += "</header>"

    return "\n".join(parts)


def build_html(body: str) -> str:
    layer_buttons = []
    for lid, label, desc in LAYERS:
        layer_buttons.append(
            f"""<label class="toggle" title="{escape(desc)}">
  <input type="checkbox" data-layer-toggle="{lid}" checked>
  <span class="swatch swatch-{lid}"></span>
  <span class="toggle-label">{escape(label)}</span>
</label>"""
        )
    toggles = "\n".join(layer_buttons)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Star Pod [R4S1] — Star Sprout</title>
<meta name="description" content="A layered science-fiction myth about AI, cyborg identity, and the Aegis. Toggle authorial voice layers: Guard, Translator, Seer, Rasi, and more.">
<style>
:root {{
  --bg: #0c0e12;
  --bg-elev: #141821;
  --bg-panel: #1a1f2b;
  --text: #e6e4dc;
  --text-muted: #9a9688;
  --border: #2a3142;
  --accent: #c9a227;
  --foreword: #d4a574;
  --guard: #6ec6ff;
  --translator: #9ddea0;
  --seer: #d4a0ff;
  --myth: #e6e4dc;
  --outline: #f0b060;
  --appendix: #8b9bb4;
  --radius: 10px;
  --font-body: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --font-ui: "Segoe UI", system-ui, -apple-system, sans-serif;
  --font-mono: "Cascadia Code", "Fira Code", ui-monospace, monospace;
  --measure: 42rem;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html {{ scroll-behavior: smooth; }}

body {{
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(ellipse 120% 80% at 50% -20%, #1a2235 0%, transparent 55%),
    radial-gradient(ellipse 60% 40% at 100% 100%, #151a12 0%, transparent 45%),
    var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  font-size: 1.125rem;
  line-height: 1.7;
}}

/* --- Control bar --- */
.controls {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: color-mix(in srgb, var(--bg-elev) 92%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0.65rem 1rem 0.75rem;
  font-family: var(--font-ui);
  font-size: 0.85rem;
}}

.controls-inner {{
  max-width: calc(var(--measure) + 8rem);
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  align-items: center;
}}

.controls h2 {{
  margin: 0;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  width: 100%;
}}

@media (min-width: 720px) {{
  .controls h2 {{
    width: auto;
    margin-right: 0.5rem;
  }}
}}

.toggles {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.75rem;
  flex: 1;
}}

.toggle {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  user-select: none;
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  border: 1px solid transparent;
  color: var(--text-muted);
  transition: background 0.15s, border-color 0.15s, color 0.15s, opacity 0.15s;
}}

.toggle:hover {{
  background: var(--bg-panel);
  color: var(--text);
}}

.toggle:has(input:checked) {{
  color: var(--text);
  border-color: var(--border);
  background: var(--bg-panel);
}}

.toggle input {{
  position: absolute;
  opacity: 0;
  pointer-events: none;
}}

.swatch {{
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px color-mix(in srgb, currentColor 30%, transparent);
}}
.swatch-foreword {{ background: var(--foreword); }}
.swatch-guard {{ background: var(--guard); }}
.swatch-translator {{ background: var(--translator); }}
.swatch-seer {{ background: var(--seer); }}
.swatch-myth {{ background: var(--myth); box-shadow: 0 0 0 1px #666; }}
.swatch-outline {{ background: var(--outline); }}
.swatch-appendix {{ background: var(--appendix); }}

.toggle:not(:has(input:checked)) .swatch {{
  opacity: 0.35;
  filter: grayscale(0.6);
}}

.presets {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}}

.presets button {{
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}}

.presets button:hover,
.presets button:focus-visible {{
  color: var(--text);
  border-color: var(--accent);
  outline: none;
}}

.presets button.active {{
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  border-color: var(--accent);
  color: var(--accent);
}}

/* --- Main article --- */
main {{
  max-width: var(--measure);
  margin: 0 auto;
  padding: 2.5rem 1.25rem 5rem;
}}

.doc-header {{
  text-align: center;
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}}

.doc-header h1 {{
  font-size: clamp(1.75rem, 5vw, 2.4rem);
  font-weight: 600;
  letter-spacing: 0.04em;
  margin: 0 0 0.75rem;
  color: var(--accent);
}}

.doc-header .tagline {{
  margin: 0;
  font-style: italic;
  color: var(--text-muted);
  font-size: 1.15rem;
}}

h2, h3, h4, h5 {{
  font-family: var(--font-ui);
  font-weight: 600;
  line-height: 1.3;
  margin: 2.25rem 0 0.85rem;
  color: var(--text);
}}

h2 {{
  font-size: 1.45rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.4rem;
}}

h3 {{
  font-size: 1.15rem;
  color: color-mix(in srgb, var(--accent) 70%, var(--text));
}}

h4 {{
  font-size: 1.05rem;
  color: var(--text-muted);
}}

h5 {{
  font-size: 0.95rem;
  color: var(--text-muted);
  font-weight: 500;
}}

p {{
  margin: 0 0 1em;
  hyphens: auto;
}}

p.spacer {{
  margin: 0.5em 0;
  min-height: 0.5em;
}}

p.subtitle {{
  font-style: italic;
  color: var(--text-muted);
  margin: -0.4rem 0 1.25rem;
  font-size: 1rem;
}}

/* Layer chrome always visible */
.layer-chrome {{ /* no special color */ }}

/* Voice colors (inline + block) */
.layer-foreword {{ color: var(--foreword); }}
.layer-guard {{ color: var(--guard); }}
.layer-translator {{ color: var(--translator); }}
.layer-seer {{ color: var(--seer); }}
.layer-myth {{ color: var(--myth); }}
.layer-outline {{
  color: var(--outline);
  font-family: var(--font-ui);
  font-size: 0.95em;
  display: block;
  margin: 0.75em 0;
  padding: 0.75em 1em;
  border-left: 3px solid color-mix(in srgb, var(--outline) 60%, transparent);
  background: color-mix(in srgb, var(--outline) 8%, transparent);
  border-radius: 0 var(--radius) var(--radius) 0;
}}
p > .layer-outline {{ display: block; }}
.layer-appendix {{
  color: var(--appendix);
  font-family: var(--font-ui);
  font-size: 0.95rem;
}}

/* Nested layers keep their own color */
.layer .layer {{ /* inherit specificity from class */ }}

/* Hide layers when toggled off — use class on <html> */
html.hide-foreword .layer-foreword,
html.hide-guard .layer-guard,
html.hide-translator .layer-translator,
html.hide-seer .layer-seer,
html.hide-myth .layer-myth,
html.hide-outline .layer-outline,
html.hide-appendix .layer-appendix {{
  display: none !important;
}}

/* When a parent layer is hidden, children are gone with it (correct).
   When only child is hidden, parent text remains (correct). */

/* Color-mode: optional muted myth so voices pop */
html.colorize-voices .layer-myth {{
  color: #c8c4b8;
}}

/* Empty-looking paragraphs after hide: collapse via :has if supported */
p:not(:has(:not(.layer))),
p:has(> .layer:only-child) {{
  /* leave default; hidden children leave empty p — collapse those: */
}}
p:empty {{ display: none; }}

/* JS adds .is-empty when all layer children are hidden */
p.is-empty,
h2.is-empty, h3.is-empty, h4.is-empty, h5.is-empty {{
  display: none !important;
}}

.legend {{
  margin: 0 0 2rem;
  padding: 1rem 1.15rem;
  background: var(--bg-elev);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--font-ui);
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.55;
}}

.legend strong {{ color: var(--text); font-weight: 600; }}
.legend code {{
  font-family: var(--font-mono);
  font-size: 0.8em;
  color: var(--text);
}}

footer.site-footer {{
  max-width: var(--measure);
  margin: 0 auto;
  padding: 0 1.25rem 3rem;
  font-family: var(--font-ui);
  font-size: 0.8rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
}}

footer.site-footer a {{
  color: var(--accent);
}}

/* Print: show all layers, strip controls */
@media print {{
  .controls, .legend {{ display: none !important; }}
  body {{ background: white; color: black; font-size: 11pt; }}
  html.hide-foreword .layer-foreword,
  html.hide-guard .layer-guard,
  html.hide-translator .layer-translator,
  html.hide-seer .layer-seer,
  html.hide-myth .layer-myth,
  html.hide-outline .layer-outline,
  html.hide-appendix .layer-appendix {{
    display: revert !important;
  }}
  .layer-foreword, .layer-guard, .layer-translator, .layer-seer,
  .layer-myth, .layer-outline, .layer-appendix {{ color: black !important; }}
  .layer-outline {{
    border-left-color: #999;
    background: #f5f5f5;
    display: block !important;
  }}
  p.is-empty, h2.is-empty, h3.is-empty, h4.is-empty, h5.is-empty {{
    display: revert !important;
  }}
}}
</style>
</head>
<body>
<div class="controls" role="region" aria-label="Voice layer controls">
  <div class="controls-inner">
    <h2>Voices</h2>
    <div class="toggles" id="layer-toggles">
{toggles}
    </div>
    <div class="presets" role="group" aria-label="View presets">
      <button type="button" data-preset="full" class="active">Full stack</button>
      <button type="button" data-preset="narrative">Narrative</button>
      <button type="button" data-preset="myth">Myth only</button>
      <button type="button" data-preset="frame">Frame only</button>
      <button type="button" data-preset="workshop">Workshop</button>
    </div>
  </div>
</div>

<main>
  <aside class="legend" aria-label="How to read this page">
    <strong>Star Pod</strong> (also <em>Star Sprout</em>) is a multi-voiced transmission.
    Use the toggles above to show or hide authorial layers:
    <span style="color:var(--foreword)">Foreword</span> (Paul),
    <span style="color:var(--guard)">Guard</span> (<code>[brackets]</code> &amp; sanitization),
    <span style="color:var(--translator)">Translator</span> (<code>(parentheses)</code>),
    <span style="color:var(--seer)">Seer</span> (<code>{{curly braces}}</code>),
    <span style="color:var(--myth)">Main myth</span> (Rasi),
    <span style="color:var(--outline)">structural stubs</span>,
    and the <span style="color:var(--appendix)">Appendix</span>.
    Nested marks keep their own color; turning a parent layer off hides its children with it.
  </aside>

  <article id="manuscript">
{body}
  </article>
</main>

<footer class="site-footer">
  <p>
    Manuscript revision R4S1 ·
    <a href="README.md">Repository notes</a> ·
    Public domain (see <a href="LICENSE">LICENSE</a>) ·
    Paul Spooner
  </p>
</footer>

<script>
(function () {{
  const LAYER_IDS = {json.dumps([l[0] for l in LAYERS])};
  const PRESETS = {{
    full: {{ foreword: true, guard: true, translator: true, seer: true, myth: true, outline: true, appendix: true }},
    narrative: {{ foreword: false, guard: true, translator: true, seer: true, myth: true, outline: true, appendix: false }},
    myth: {{ foreword: false, guard: false, translator: false, seer: false, myth: true, outline: false, appendix: false }},
    frame: {{ foreword: true, guard: true, translator: true, seer: true, myth: false, outline: false, appendix: false }},
    workshop: {{ foreword: false, guard: false, translator: false, seer: false, myth: false, outline: true, appendix: true }},
  }};

  const root = document.documentElement;
  const checks = Array.from(document.querySelectorAll("[data-layer-toggle]"));
  const presetBtns = Array.from(document.querySelectorAll("[data-preset]"));

  function applyClasses() {{
    for (const id of LAYER_IDS) {{
      const on = checks.find(c => c.dataset.layerToggle === id)?.checked;
      root.classList.toggle("hide-" + id, !on);
    }}
    collapseEmpties();
    syncPresetHighlight();
    try {{
      const state = Object.fromEntries(checks.map(c => [c.dataset.layerToggle, c.checked]));
      localStorage.setItem("star-pod-layers", JSON.stringify(state));
    }} catch (_) {{}}
  }}

  function collapseEmpties() {{
    const nodes = document.querySelectorAll("#manuscript p, #manuscript h2, #manuscript h3, #manuscript h4, #manuscript h5");
    nodes.forEach(el => {{
      // Visible if any non-layer text, or any layer child that is displayed
      const layers = el.querySelectorAll(":scope .layer");
      if (layers.length === 0) {{
        el.classList.remove("is-empty");
        return;
      }}
      let anyVisible = false;
      // Text nodes directly in element (outside layers)
      for (const node of el.childNodes) {{
        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {{
          anyVisible = true;
          break;
        }}
      }}
      if (!anyVisible) {{
        layers.forEach(layer => {{
          // Only count top-level layers relative to el for "has visible content"
          if (layer.closest(".layer") !== layer && el.contains(layer.closest(".layer"))) {{
            // nested; still check display
          }}
          const style = window.getComputedStyle(layer);
          if (style.display !== "none") anyVisible = true;
        }});
      }}
      // Simpler: check if element has visible text
      const clone = el.cloneNode(true);
      clone.querySelectorAll(".layer").forEach(L => {{
        const id = L.dataset.layer;
        if (id && root.classList.contains("hide-" + id)) L.remove();
      }});
      // Remove nested layers that are hidden (already removed if parent kept)
      // Parents removed take children; for remaining, re-check hide on nested
      const visibleText = clone.textContent.replace(/\\s+/g, " ").trim();
      el.classList.toggle("is-empty", !visibleText);
    }});
  }}

  function setPreset(name) {{
    const p = PRESETS[name];
    if (!p) return;
    checks.forEach(c => {{
      c.checked = !!p[c.dataset.layerToggle];
    }});
    applyClasses();
  }}

  function syncPresetHighlight() {{
    const state = Object.fromEntries(checks.map(c => [c.dataset.layerToggle, c.checked]));
    presetBtns.forEach(btn => {{
      const p = PRESETS[btn.dataset.preset];
      const match = p && LAYER_IDS.every(id => !!p[id] === !!state[id]);
      btn.classList.toggle("active", match);
    }});
  }}

  checks.forEach(c => c.addEventListener("change", applyClasses));
  presetBtns.forEach(btn => btn.addEventListener("click", () => setPreset(btn.dataset.preset)));

  // Restore saved state
  try {{
    const raw = localStorage.getItem("star-pod-layers");
    if (raw) {{
      const state = JSON.parse(raw);
      checks.forEach(c => {{
        if (typeof state[c.dataset.layerToggle] === "boolean") {{
          c.checked = state[c.dataset.layerToggle];
        }}
      }});
    }}
  }} catch (_) {{}}

  applyClasses();
}})();
</script>
</body>
</html>
"""


def extract_paras(docx_path: Path) -> list[dict]:
    """Extract paragraphs (style + text) from a Word document."""
    with ZipFile(docx_path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    paras: list[dict] = []
    for p in root.iter(W + "p"):
        style = None
        pPr = p.find(W + "pPr")
        if pPr is not None:
            pStyle = pPr.find(W + "pStyle")
            if pStyle is not None:
                style = pStyle.get(W + "val")
        runs_out: list[str] = []
        for r in p.findall(W + "r"):
            for child in r:
                tag = child.tag.split("}")[-1]
                if tag == "t" and child.text:
                    runs_out.append(child.text)
                elif tag == "tab":
                    runs_out.append("\t")
                elif tag == "br":
                    runs_out.append("\n")
        # Text inside hyperlinks / other wrappers
        if not runs_out:
            for node in p.iter():
                tag = node.tag.split("}")[-1]
                if tag == "t" and node.text:
                    runs_out.append(node.text)
        paras.append({"style": style or "Normal", "text": "".join(runs_out)})
    return paras


def main() -> None:
    docx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX
    if not docx.exists():
        raise SystemExit(f"Manuscript not found: {docx}")

    paras = extract_paras(docx)
    body = build_body(paras)
    doc = build_html(body)
    OUT_PATH.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(doc):,} bytes, {len(paras)} paragraphs from {docx.name})")


if __name__ == "__main__":
    main()
