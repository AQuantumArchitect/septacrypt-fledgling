"""Story endpoints over live HTTP (additive on the frozen v1 surface)."""
import pytest


@pytest.fixture(scope="module")
def story_sid(client):
    status, body = client.post("/v1/sessions", {"story": "starpod", "seed": 7})
    assert status == 200 and body["ok"]
    return body["session_id"]


def test_create_story_session_returns_render_state(story_sid, client):
    status, body = client.get(f"/v1/sessions/{story_sid}/status")
    assert status == 200
    assert body["state"]["schema_version"] == "fledgeling.render.v2"


def test_story_endpoint_shape(story_sid, client):
    status, body = client.get(f"/v1/sessions/{story_sid}/story")
    assert status == 200
    story = body["story"]
    assert story["story_id"] == "rasir.starpod.v1"
    assert story["run_state"] in ("coherent", "complete")
    assert [s["name"] for s in story["stages"]][:2] == ["Egg", "Gestation"]
    assert story["beats"]["total_waypoints"] == 9
    egg = story["stages"][0]
    assert set(egg) >= {"fog", "inked", "effective_mask", "legal_next_masks",
                        "forbidden_masks", "canonical_mask"}


def test_choose_over_http(story_sid, client):
    status, body = client.post(
        f"/v1/sessions/{story_sid}/choose", {"stage": "Aegis", "strand": "entity"})
    assert status == 200
    assert body["result"]["inked"]["entity"] in (-1, 0, 1)
    assert body["story"]["journal_length"] >= 1


def test_choose_validates_body(story_sid, client):
    status, body = client.post(f"/v1/sessions/{story_sid}/choose", {"stage": "Aegis"})
    assert status == 400
    status, body = client.post(
        f"/v1/sessions/{story_sid}/choose", {"stage": "Nowhere", "strand": "x"})
    assert status == 400


def test_branches_empty_until_revival(story_sid, client):
    status, body = client.get(f"/v1/sessions/{story_sid}/branches")
    assert status == 200
    assert body["branches"] == []


def test_plain_sessions_404_story_routes(client):
    status, body = client.post("/v1/sessions", {"mode": "reactor", "seed": 1})
    sid = body["session_id"]
    for method, path in (
        ("GET", f"/v1/sessions/{sid}/story"),
        ("GET", f"/v1/sessions/{sid}/branches"),
        ("POST", f"/v1/sessions/{sid}/choose"),
        ("POST", f"/v1/sessions/{sid}/revive"),
    ):
        status, body = client.request(method, path, {"stage": "x", "strand": "y"} if method == "POST" else None)
        assert status in (400, 404)
        if status == 404:
            assert body["error"]["kind"] in ("NotAStorySession", "NotFound")
    client.delete(f"/v1/sessions/{sid}")


def test_unknown_story_rejected(client):
    status, body = client.post("/v1/sessions", {"story": "moby-dick"})
    assert status == 400
    assert body["error"]["kind"] == "UnknownStory"


def test_revive_on_coherent_is_400(story_sid, client):
    status, body = client.post(f"/v1/sessions/{story_sid}/revive")
    assert status == 400
