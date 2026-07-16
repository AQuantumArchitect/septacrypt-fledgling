"""Contract tests for fledgeling.api.v1 — every endpoint, error map, determinism."""
import concurrent.futures

from septacrypt_core.api.schema import RENDER_SCHEMA_VERSION, validate_render_state
from septacrypt_core.world.transaction import TransactionError

from septacrypt_fledgling import API_VERSION
from septacrypt_fledgling.server.errors import map_exception


def _create(client, **params):
    status, body = client.post("/v1/sessions", params)
    assert status == 200, body
    assert body["ok"] and body["api"] == API_VERSION
    return body["session_id"], body["state"]


def test_create_and_status_schema(client):
    session_id, state = _create(client, mode="reactor", seed=7)
    assert state["schema_version"] == RENDER_SCHEMA_VERSION
    assert validate_render_state(state) == []
    status, body = client.get(f"/v1/sessions/{session_id}/status?observer=player")
    assert status == 200
    assert body["state"]["meta"]["observer"] == "player"


def test_wait_look_stir_loop(client):
    session_id, _ = _create(client, mode="ship", seed=3)
    status, body = client.post(f"/v1/sessions/{session_id}/wait", {"steps": 2})
    assert status == 200 and body["ok"]
    turn_after_wait = body["state"]["meta"]["turn"]

    status, body = client.post(
        f"/v1/sessions/{session_id}/look",
        {"observer_id": "player", "target_role": "nav_lens", "zone": "Navigation"},
    )
    assert status == 200 and body["ok"]
    assert body["state"]["meta"]["turn"] > turn_after_wait

    status, body = client.post(f"/v1/sessions/{session_id}/stir", {})
    assert status == 200 and body["ok"]


def test_quests_history_weave_schema_endpoints(client):
    session_id, _ = _create(client, mode="ship", seed=11)
    status, body = client.get(f"/v1/sessions/{session_id}/quests")
    assert status == 200 and isinstance(body["quests"], list) and body["victory"] is False

    status, body = client.get(f"/v1/sessions/{session_id}/history")
    assert status == 200 and isinstance(body["history"], list) and body["physics_hash"]

    status, body = client.post(
        f"/v1/sessions/{session_id}/weave", {"start_mask": 0b000, "end_mask": 0b011}
    )
    assert status == 200 and isinstance(body["story"], str) and body["story"]

    status, body = client.get("/v1/schema")
    assert status == 200
    assert body["render_schema_version"] == RENDER_SCHEMA_VERSION
    assert "GameSession.status payload" in body["render_state_doc"]


def test_report_updates_target_only(client):
    session_id, _ = _create(client, mode="reactor", seed=5)
    status, body = client.post(
        f"/v1/sessions/{session_id}/report",
        {"source": "alice", "target": "bob", "role": "valve_17"},
    )
    assert status == 200 and body["ok"]


def test_error_map():
    status, kind, msg = map_exception(TransactionError("residual too large"))
    assert status == 409 and kind == "TransactionError" and "unchanged" in msg
    status, kind, _ = map_exception(ValueError("bad mode"))
    assert status == 400 and kind == "ValueError"


def test_http_errors(client):
    status, body = client.get("/v1/sessions/deadbeef00000000/status")
    assert status == 404 and body["error"]["kind"] == "UnknownSession"

    status, body = client.post("/v1/sessions", {"mode": "flying-castle"})
    assert status == 400  # GameSession rejects unknown mode

    status, body = client.post("/v1/sessions", {"cheat_codes": True})
    assert status == 400 and "unknown session params" in body["error"]["message"]

    session_id, _ = _create(client, mode="reactor", seed=1)
    status, body = client.post(f"/v1/sessions/{session_id}/look", {})
    assert status == 400 and "target_role" in body["error"]["message"]

    status, body = client.get("/v1/nope")
    assert status == 404

    status, body = client.delete(f"/v1/sessions/{session_id}")
    assert status == 200
    status, body = client.get(f"/v1/sessions/{session_id}/status")
    assert status == 404


def test_seed_determinism_over_http(client):
    hashes = []
    for _ in range(2):
        session_id, _ = _create(client, mode="ship", seed=42)
        client.post(f"/v1/sessions/{session_id}/wait", {"steps": 3})
        client.post(
            f"/v1/sessions/{session_id}/look",
            {"observer_id": "p", "target_role": "core_valve", "zone": "Reactor_Core"},
        )
        _, body = client.get(f"/v1/sessions/{session_id}/history")
        hashes.append(body["physics_hash"])
    assert hashes[0] == hashes[1]


def test_concurrent_sessions(client):
    ids = [_create(client, mode="reactor", seed=i)[0] for i in range(4)]

    def hammer(session_id):
        for _ in range(5):
            status, body = client.post(f"/v1/sessions/{session_id}/wait", {})
            assert status == 200, body
        _, body = client.get(f"/v1/sessions/{session_id}/status")
        return body["state"]["meta"]["turn"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        turns = list(pool.map(hammer, ids))
    assert all(t >= 5 for t in turns)
