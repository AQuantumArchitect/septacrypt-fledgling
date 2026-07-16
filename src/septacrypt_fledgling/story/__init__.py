"""Live Story Physics — a partially written book as a quantum world.

StorySpec (spec.py) declares the book's structure; ingest.py reads the
archived manuscript into passages; compile.py turns a StorySpec into a
septacrypt-core WorldSpec. All lore content lives in starpod.py — the
engines below this package stay lore-free (ADR-001).
"""
from .spec import (
    BeatSpec,
    CausalLinkSpec,
    PassageSpec,
    StageSpec,
    StorySpec,
    StrandSpec,
    VoiceSpec,
)
from .compile import StoryCompiler, compile_story

__all__ = [
    "BeatSpec",
    "CausalLinkSpec",
    "PassageSpec",
    "StageSpec",
    "StorySpec",
    "StrandSpec",
    "VoiceSpec",
    "StoryCompiler",
    "compile_story",
]
