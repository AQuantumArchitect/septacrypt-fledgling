"""Narrator gates: deterministic fallback, register selection, mocked API
round-trip (including refusal -> fallback). No network, ever."""
import urllib.error

import pytest

from septacrypt_fledgling.narrator import Narrator
from septacrypt_fledgling.narrator.client import NarratorClient
from septacrypt_fledgling.narrator.fallback import narrate_offline
from septacrypt_fledgling.narrator.voices import REGISTERS, system_prompt
from septacrypt_fledgling.story.session import StorySession
from septacrypt_fledgling.story.starpod import STAR_POD

SEED = 7


@pytest.fixture(scope="module")
def session():
    s = StorySession(STAR_POD, seed=SEED)
    s.wait(steps=2)
    s.choose("Aegis", "entity")
    return s


def test_offline_narration_is_deterministic_and_in_register():
    inked = {"entity": 1, "shield": 0, "containment": 0}
    a = narrate_offline(STAR_POD, "Aegis", inked, "guard", "choose", "entity")
    b = narrate_offline(STAR_POD, "Aegis", inked, "guard", "choose", "entity")
    assert a == b
    assert a.startswith("[") and "checksum" in a  # Guard: contain
    seer = narrate_offline(STAR_POD, "Aegis", inked, "seer", "choose", "entity")
    assert seer.startswith("{") and "Rejoyce" in seer  # Seer: revere
    rasi = narrate_offline(STAR_POD, "Aegis", inked, "rasi", "wait")
    assert "time passed" in rasi  # Rasi: witness


def test_glosses_come_from_the_strand_specs():
    up = narrate_offline(STAR_POD, "Aegis", {"containment": 1}, "translator", "choose", "containment")
    down = narrate_offline(STAR_POD, "Aegis", {"containment": -1}, "translator", "choose", "containment")
    assert "contained within" in up
    assert "runs loose" in down


def test_system_prompts_carry_the_registers():
    for voice in REGISTERS:
        sp = system_prompt(voice)
        assert "150 words" in sp
    assert "checksum" in system_prompt("guard")
    with pytest.raises(ValueError):
        system_prompt("ishmael")


def test_narrate_uses_fallback_offline(session):
    n = Narrator(mode="offline")
    e = n.narrate(session, voice="rasi")
    assert e.source == "fallback"
    assert e.stamp_id and e.physics_hash
    # cache: same stamp+hash+voice reuses the entry object
    assert n.narrate(session, voice="rasi") is e
    # different voice narrates fresh
    assert n.narrate(session, voice="guard") is not e


def test_api_mode_round_trip_and_refusal(session):
    calls = []

    def ok_transport(payload):
        calls.append(payload)
        return {"stop_reason": "end_turn",
                "content": [{"type": "text", "text": "And so the Entity held."}]}

    n = Narrator(mode="api", client=NarratorClient(transport=ok_transport))
    e = n.narrate(session, voice="rasi")
    assert e.source == "api" and e.text == "And so the Entity held."
    payload = calls[0]
    assert payload["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Rasi" in payload["system"][0]["text"]
    user_prompt = payload["messages"][0]["content"]
    assert "STAGE: Aegis" in user_prompt

    def refusing_transport(payload):
        return {"stop_reason": "refusal", "content": []}

    n2 = Narrator(mode="api", client=NarratorClient(transport=refusing_transport))
    e2 = n2.narrate(session, voice="rasi")
    assert e2.source == "fallback"  # refusal degrades to offline text


def test_api_errors_degrade_to_fallback(session):
    def broken_transport(payload):
        raise urllib.error.HTTPError("url", 400, "boom", {}, None)

    n = Narrator(mode="api", client=NarratorClient(transport=broken_transport))
    e = n.narrate(session, voice="translator")
    assert e.source == "fallback"
