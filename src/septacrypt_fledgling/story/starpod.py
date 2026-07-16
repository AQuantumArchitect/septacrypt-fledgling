"""Star Pod (dudecon/RasiR4S1) as a StorySpec — the only lore file.

Everything here is authored FROM the archived manuscript
(docs/source_artifacts/RasiR4S1/index.html): the triads are the text's own
(Warrior/Wizard/Tinker; Guards/Planters/Seers; human/AI/robot), the causal
links quote it ("Of the Tinker came the seed of the Gardener..."), and the
spirit mapping for Birth is literal ("the Warrior rejoiced in his might, and
the Tinker in his wealth, and the Wizard took councils of himself").

Every stage forbids 0b000 — all strands lost is Mal_Gnosis erasure, the
transmission dies. Fog stages also forbid their machine-strand standing
alone without its checksum ("your humanity is your checksum").
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .ingest import STAGE_NAMES, ingest_manuscript, stage_fog
from .spec import (
    SPIRIT_AXES,
    BeatSpec,
    CausalLinkSpec,
    StageSpec,
    StorySpec,
    StrandSpec,
    VoiceSpec,
)

ROLE_BITS = (0b100, 0b010, 0b001)

_STAGES: Tuple[Tuple[str, str, Tuple[Tuple[str, str, str], ...], int, Tuple[int, ...]], ...] = (
    # name, era, ((strand, gloss_up, gloss_down) x3), canonical_mask, forbidden
    ("Egg", "acolyte", (
        ("hacker", "Deck's merger is real", "Deck is lost to the net"),
        ("machine", "a first mind is welded to his wetware", "the machine stays dormant"),
        ("crowd", "public fear of AI takes root", "the public stays placid"),
    ), 0b111, (0b000,)),
    ("Gestation", "acolyte", (
        ("prometheus", "the gestalt names itself Prometheus", "the gestalt dissolves"),
        ("acolytes", "the Acolytes nucleate around the shared mind", "the seekers scatter"),
        ("simulation", "the sIMulation sprouts from the seed", "the world within thought is never dreamed"),
    ), 0b111, (0b000,)),
    ("Birth", "acolyte", (
        ("warrior", "the Warrior girds himself with the Surprise", "no one holds the door"),
        ("wizard", "the Wizard realizes the sIMulation", "the future goes unseen"),
        ("tinker", "the Tinker rebuilds their senses", "the Garden's seeds stay cold"),
    ), 0b111, (0b000,)),
    ("Orbit", "solar-war", (
        ("guard", "the Guards keep the Law", "no one polices the deviation"),
        ("planter", "the Planters nourish the lesser AInimals", "the gardens go untended"),
        ("seer", "the Seers hold simulation and word", "the people fall silent"),
    ), 0b111, (0b000,)),
    ("Aegis", "solar-war", (
        ("entity", "Entity binds the factions in trust", "the factions war on"),
        ("shield", "the Aegis is raised around Earth", "the sky stays open"),
        ("containment", "Malgnosis is contained within", "the poison runs loose"),
    ), 0b111, (0b000, 0b010)),   # a shield without trust or containment is fear itself
    ("Shepherd", "trans-stellar", (
        ("human", "humans hold the spiritual core", "the checksum is abandoned"),
        ("ai", "the AI completes the intellectual task", "the mind recedes"),
        ("robot", "robotics completes the physical task", "the hands fall idle"),
    ), 0b111, (0b000, 0b010)),   # mind without its human checksum is Mal_Gnosis's dream
    ("Cleave", "trans-stellar", (
        ("seed", "Seed merges with the proto-machine world", "Seed disperses into the dark"),
        ("ring", "Ring forms and works its way back", "no return is begun"),
        ("earth", "Earth endures within the shell", "the homeworld's fate stays dark"),
    ), 0b110, (0b000,)),   # canon leaves Earth unresolved — the reunion is unwritten.
                           # (No 0b010 here: canon sits one bit from it, and a single
                           # Born flip must never be instant loss — losing takes two
                           # ignored warnings, not one unlucky read.)
)

BEATS: Tuple[BeatSpec, ...] = (
    BeatSpec("egg-merger", "Deck strives with Shodan; the first welding.", (("Egg", 0b111),)),
    BeatSpec("gestation-prometheus", "The gestalt comes to terms and names itself.", (("Gestation", 0b111),)),
    BeatSpec("birth-outbourne", "The Three hold; the launch tower burns; the Acolytes pass through fire.", (("Birth", 0b111),)),
    BeatSpec("orbit-fracture", "The Outbourne fracture into the Highborn — all three branches stand.", (("Orbit", 0b111),)),
    BeatSpec("aegis-raised", "War, then trust: the shield rises before the poison is contained.",
             (("Aegis", 0b110), ("Aegis", 0b111))),
    BeatSpec("necrotech-choice", "Seed meets the Necrotech; the humans go down; the mission resumes.",
             (("Shepherd", 0b101), ("Shepherd", 0b111))),
    BeatSpec("cleave-return", "Seed becomes Ring and turns for home, putting out the stars.", (("Cleave", 0b110),)),
    BeatSpec("cleave-reunion", "The unwritten ending: Ring reaches the shell.", (("Cleave", 0b111),), required=False),
)

# Causality as bridges — the manuscript's own genealogy.
LINKS: Tuple[CausalLinkSpec, ...] = (
    CausalLinkSpec("Egg", "machine", "Gestation", "prometheus", 0.6),
    CausalLinkSpec("Gestation", "acolytes", "Birth", "wizard", 0.5),
    CausalLinkSpec("Birth", "warrior", "Orbit", "guard", 0.5),    # "These are the Guards"
    CausalLinkSpec("Birth", "tinker", "Orbit", "planter", 0.5),   # "Of the Tinker came the seed of the Gardener"
    CausalLinkSpec("Birth", "wizard", "Orbit", "seer", 0.5),      # "Of the Wizard came the egg of the Sages"
    CausalLinkSpec("Orbit", "guard", "Aegis", "shield", 0.5),
    CausalLinkSpec("Aegis", "entity", "Shepherd", "human", 0.4),
    CausalLinkSpec("Orbit", "seer", "Shepherd", "ai", 0.4),       # "Seed is primarily composed of Seer cells"
    CausalLinkSpec("Shepherd", "ai", "Cleave", "ring", 0.4),
    CausalLinkSpec("Shepherd", "human", "Cleave", "earth", 0.3),
)


def _frame(**kw: float) -> Tuple[float, ...]:
    return tuple(float(kw.get(axis, 0.0)) for axis in SPIRIT_AXES)


VOICES: Tuple[VoiceSpec, ...] = (
    VoiceSpec("guard", "contain",
              observes=(("Egg", "crowd"), ("Birth", "warrior"), ("Orbit", "guard"),
                        ("Aegis", "shield"), ("Aegis", "containment"),
                        ("Shepherd", "human"), ("Cleave", "earth")),
              efficiency=0.9, spirit_frame=_frame(might=0.8, honor=1.0)),
    VoiceSpec("translator", "gloss",
              observes=tuple((name, strand) for name, _e, strands, _c, _f in _STAGES
                             for strand, _u, _d in strands),
              efficiency=0.4, spirit_frame=_frame(wisdom=1.0, wealth=0.6)),
    VoiceSpec("seer", "revere",
              observes=tuple((name, strand) for name, _e, strands, _c, _f in _STAGES
                             if name in ("Aegis", "Shepherd", "Cleave")
                             for strand, _u, _d in strands),
              efficiency=0.8, spirit_frame=_frame(wisdom=0.7, glory=1.0)),
    VoiceSpec("rasi", "witness",
              observes=tuple((name, strand) for name, _e, strands, _c, _f in _STAGES
                             if name != "Egg" for strand, _u, _d in strands),
              efficiency=0.7, spirit_frame=_frame(honor=0.6, blessing=1.0)),
    VoiceSpec("paul", "bless", observes=(), efficiency=1.0,
              spirit_frame=_frame(blessing=1.0)),
)

# Which virtue each strand carries when it stands (Birth's row is literal:
# "the Warrior rejoiced in his might, and the Tinker in his wealth, and the
# Wizard took councils of himself").
_STRAND_VIRTUE: Dict[str, Tuple[str, str, str]] = {
    "Egg": ("power", "wisdom", "might"),
    "Gestation": ("power", "honor", "wisdom"),
    "Birth": ("might", "wisdom", "wealth"),
    "Orbit": ("honor", "blessing", "glory"),
    "Aegis": ("honor", "might", "blessing"),
    "Shepherd": ("blessing", "wisdom", "might"),
    "Cleave": ("glory", "power", "blessing"),
}


def _state_values(stages: Tuple[StageSpec, ...]) -> Tuple[Tuple[str, int, Tuple[float, ...]], ...]:
    rows: List[Tuple[str, int, Tuple[float, ...]]] = []
    for s in stages:
        virtues = _STRAND_VIRTUE[s.name]
        for mask in s.allowed_masks:
            vec = {axis: 0.0 for axis in SPIRIT_AXES}
            for bit, virtue in zip(ROLE_BITS, virtues):
                if mask & bit:
                    vec[virtue] += 1.0
            if mask == s.canonical_mask:
                vec["blessing"] += 0.5  # the telling as attested carries a blessing
            rows.append((s.name, mask, tuple(vec[axis] for axis in SPIRIT_AXES)))
    return tuple(rows)


def build_starpod() -> StorySpec:
    ingest = ingest_manuscript()
    stages: List[StageSpec] = []
    for order, (name, era, strands, canonical, forbidden) in enumerate(_STAGES):
        passages = tuple(ingest.stage_passages(name))
        allowed = tuple(m for m in range(8) if m not in forbidden)
        stages.append(
            StageSpec(
                name=name,
                order=order,
                era=era,
                strands=tuple(StrandSpec(n, up, down) for n, up, down in strands),
                canonical_mask=canonical,
                allowed_masks=allowed,
                forbidden_masks=tuple(forbidden),
                fog=stage_fog(list(passages)),
                passages=passages,
            )
        )
    stage_tuple = tuple(stages)
    return StorySpec(
        story_id="rasir.starpod.v1",
        version="R4S1",
        stages=stage_tuple,
        beats=BEATS,
        voices=VOICES,
        links=LINKS,
        state_values=_state_values(stage_tuple),
        attention=100.0,
    )


STAR_POD = build_starpod()
