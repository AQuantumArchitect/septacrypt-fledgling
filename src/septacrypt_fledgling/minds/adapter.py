"""M2.4 convergence probe: hold observer beliefs in umwelt's WorldSession.

septacrypt-core's ObserverBeliefStore is a hand-rolled first-moment belief
snapshot. umwelt's WorldSession is the real thing: N private belief engines
over one ground truth, with channel masks and self-action hygiene. This
adapter maps septacrypt's typed epistemic events (LOOK outcomes, reports)
onto WorldSession observations so the two backends can be compared.

Wraps `umwelt.host` — never reimplements it (plan §11 rule: minds/ wraps
umwelt.host). Vocabulary per ADR-001: this module speaks umwelt's names
module-qualified and exports neither.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from umwelt.host.session import WorldSession
from umwelt.spec.schema import BindingSpec, DomainSpec, DriverSpec, NodeSpec

TICK_S = 60.0


def station_beliefs_spec(roles: Tuple[str, ...], name: str = "septacrypt-station") -> DomainSpec:
    """One belief node per septacrypt role; channel see_{role} per node.

    Belief value is the P(+pole) of that role in [0, 1] (z = 2v - 1).
    """
    nodes = [NodeSpec("station", parent=None, kind="root", roles=("state",))]
    for role in roles:
        nodes.append(
            NodeSpec(
                role,
                parent="station",
                kind="device",
                roles=("state",),
            )
        )
    # strength 0.9: a direct LOOK at a device is near-authoritative — the fog
    # example's 0.35 scout strength can't pull a belief across the midpoint.
    bindings = tuple(
        BindingSpec(
            f"see_{role}",
            zone=role,
            role="state",
            normalizer="binary",
            force_observe=True,
            efficiency=1.0,
            strength=0.9,
        )
        for role in roles
    )
    return DomainSpec(
        name=name,
        nodes=tuple(nodes),
        bridges=(),
        bindings=bindings,
        outputs=(),
        drivers=(DriverSpec("tick", node="_clock", role="phase", period_s=TICK_S),),
        anchors={},
    )


class UmweltMindsAdapter:
    """Private per-observer belief fields for a septacrypt zone's roles."""

    def __init__(self, roles: Tuple[str, ...]):
        self.roles = tuple(roles)
        self.session = WorldSession().register_world(station_beliefs_spec(self.roles))

    def add_observer(self, observer_id: str) -> None:
        self.session.add_mind(observer_id)

    def saw(self, observer_id: str, role: str, outcome_z: float, confidence: float = 1.0) -> None:
        """A LOOK outcome lands only in the looker's private mind."""
        value = (float(outcome_z) + 1.0) / 2.0
        self.session.observe_raw(observer_id, f"see_{role}", value, confidence=confidence)

    def heard(self, target_observer: str, role: str, reported_z: float, confidence: float = 0.35) -> None:
        """A report lands in the *target's* mind at reduced confidence."""
        value = (float(reported_z) + 1.0) / 2.0
        self.session.observe_raw(target_observer, f"see_{role}", value, confidence=confidence)

    def step(self, n: int = 1) -> None:
        self.session.step_turn(n)

    def belief_z(self, observer_id: str, role: str) -> Optional[Tuple[float, float]]:
        """(z, confidence) of observer's belief about role, or None if silent."""
        beliefs = self.session.beliefs(observer_id)
        for key, b in beliefs.items():
            if key.startswith(f"{role}."):
                return (2.0 * float(b.value) - 1.0, float(b.confidence))
        return None

    def beliefs_snapshot(self, observer_id: str) -> Dict[str, Tuple[float, float]]:
        out: Dict[str, Tuple[float, float]] = {}
        for role in self.roles:
            bz = self.belief_z(observer_id, role)
            if bz is not None:
                out[role] = bz
        return out
