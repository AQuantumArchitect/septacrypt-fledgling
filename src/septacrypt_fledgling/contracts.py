"""Typed face-edge contracts for the seven-face Septacrypt architecture.

Each Protocol names the *minimum* surface one face may demand of another
(FLEDGELING_SEPTACRYPT_PLAN.md §2.2). Shipped classes are declared
conformant by tests (tests/test_face_contracts.py), never by inheritance —
the engines must not import this repo.

Thin and honest: a Protocol here documents an edge that exists in running
code today. Edges that are still design (Architect auto-compile, retro-sim)
get no Protocol until they run.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable


@runtime_checkable
class StructureFace(Protocol):
    """Face 1 — Universal Architect. Edge: Architect → Dynamics (compile
    declared hierarchies into entity references)."""

    def compile_hierarchy(self, root: Any) -> Any: ...


@runtime_checkable
class DynamicsFace(Protocol):
    """Face 2 — SpaceWheat / cumulant substrate. Edge: Dynamics → Belief
    (evolve and expose observable coordinates; never leak ground truth
    directly to a mind)."""

    n_qubits: int
    qubit_roles: Any

    def step(self, dt_scale: float = ...) -> Any: ...
    def role_bloch(self, role: str) -> Any: ...
    def snapshot(self) -> Dict[str, Any]: ...


@runtime_checkable
class BeliefFace(Protocol):
    """Face 3 — umwelt. Edge: observations in, private beliefs out."""

    def observe(self, observer_id: str, channel: str, value: float, confidence: float, t: Any = ...) -> Any: ...
    def beliefs(self, observer_id: str, query: Optional[str] = ...) -> Dict[str, Any]: ...


@runtime_checkable
class KairosFace(Protocol):
    """Face 4 — Berry Tape. Edge: Kairos → History (geometric/process
    coordinates attached to durable stamps)."""

    def coordinate(self, cluster: Any) -> Dict[str, Any]: ...


@runtime_checkable
class HistoryFace(Protocol):
    """Face 5 — Knot Ledger. Edge: History → Agency (expose witnessed
    history and state roots)."""

    def history(self, branch: Optional[str] = ...) -> List[Dict[str, Any]]: ...
    def physics_hash(self) -> str: ...


@runtime_checkable
class AgencyFace(Protocol):
    """Face 6 — Fledgeling. The playable surface (what the HTTP host serves)."""

    def wait(self, dt_scale: Optional[float] = ..., *, steps: int = ..., zone: Optional[str] = ..., observer_id: str = ...) -> Dict[str, Any]: ...
    def look(self, observer_id: str, target_role: str, *, zone: Optional[str] = ..., strength: float = ...) -> Dict[str, Any]: ...
    def stir(self, observer_id: str = ...) -> Dict[str, Any]: ...
    def status(self, observer_id: str = ..., *, zone: Optional[str] = ..., full_ship: bool = ...) -> Dict[str, Any]: ...
    def quest_status(self) -> List[Dict[str, Any]]: ...
    def victory(self) -> bool: ...


@runtime_checkable
class MeaningFace(Protocol):
    """Face 7 — Spirit Cube. Edge: Meaning ↔ all (rank legal options;
    physics constrains, spirit ranks, narrative expresses — spirit must
    never legalize an invalid transition)."""

    def dot(self, other: Any) -> float: ...
