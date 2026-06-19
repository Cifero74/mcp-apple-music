import asyncio

import httpx
import pytest

from mcp_apple_music.client import AppleMusicClient
from mcp_apple_music.responses import AppleMusicAPIError, clean_params, structured_response


class FakeAuth:
    def get_auth_headers(self):
        return {
            "Authorization": "Bearer developer-token",
            "Music-User-Token": "user-token",
        }

    def get_catalog_headers(self):
        return {"Authorization": "Bearer developer-token"}


def run(coro):
    return asyncio.run(coro)


def client_for(handler):
    transport = httpx.MockTransport(handler)
    return AppleMusicClient(FakeAuth(), client_factory=lambda: httpx.AsyncClient(transport=transport))


def json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_clean_params_preserves_falsey_values():
    assert clean_params({"a": None, "b": "", "c": 0, "d": False}) == {
        "b": "",
        "c": 0,
        "d": False,
    }


def test_catalog_get_omits_music_user_token_and_strips_none_params():
    seen = {}

    def handler(request):
        seen["headers"] = request.headers
        seen["url"] = request.url
        return json_response({"data": [{"id": "1", "type": "songs"}]})

    client = client_for(handler)
    payload = run(client.get("/catalog/us/songs", {"ids": "1", "include": None}, user_auth=False))

    assert payload["data"][0]["id"] == "1"
    assert seen["headers"]["Authorization"] == "Bearer developer-token"
    assert "Music-User-Token" not in seen["headers"]
    assert dict(seen["url"].params) == {"ids": "1"}


def test_post_includes_user_token_and_content_type():
    seen = {}

    def handler(request):
        seen["headers"] = request.headers
        seen["body"] = request.content
        return json_response({"data": [{"id": "p.1"}]})

    client = client_for(handler)
    payload = run(client.post("/me/library/playlists", {"attributes": {"name": "Mix"}}))

    assert payload["data"][0]["id"] == "p.1"
    assert seen["headers"]["Music-User-Token"] == "user-token"
    assert seen["headers"]["Content-Type"] == "application/json"
    assert b"Mix" in seen["body"]


def test_post_many_reuses_request_helper_for_each_body():
    bodies = []

    def handler(request):
        bodies.append(request.content)
        return json_response({"data": [{"id": str(len(bodies))}]})

    client = client_for(handler)
    payloads = run(
        client.post_many(
            "/me/library/playlists/p.1/tracks",
            [{"data": [{"id": "1"}]}, {"data": [{"id": "2"}]}],
        )
    )

    assert payloads == [{"data": [{"id": "1"}]}, {"data": [{"id": "2"}]}]
    assert b'"1"' in bodies[0]
    assert b'"2"' in bodies[1]


def test_errors_preserve_status_and_body():
    def handler(request):
        return json_response(
            {"errors": [{"title": "Forbidden", "detail": "No music user token"}]},
            status_code=403,
        )

    client = client_for(handler)

    with pytest.raises(AppleMusicAPIError) as error:
        run(client.get("/me/library/songs"))

    assert error.value.status_code == 403
    assert error.value.method == "GET"
    assert error.value.path == "/me/library/songs"
    assert error.value.message == "No music user token"


def test_request_structured_wraps_raw_payload():
    def handler(request):
        return json_response({"data": [{"id": "1"}], "meta": {"total": 1}, "next": "/next"})

    client = client_for(handler)
    payload = run(client.request_structured("GET", "/catalog/us/songs", {"ids": "1"}))

    assert payload["request"] == {
        "method": "GET",
        "path": "/catalog/us/songs",
        "params": {"ids": "1"},
    }
    assert payload["data"] == [{"id": "1"}]
    assert payload["raw"]["meta"]["total"] == 1


def test_get_all_pages_uses_offsets_until_next_disappears():
    offsets = []

    def handler(request):
        offset = int(request.url.params.get("offset", 0))
        offsets.append(offset)
        if offset == 0:
            return json_response({"data": [{"id": "1"}], "next": "/page-2"})
        return json_response({"data": [{"id": "2"}]})

    client = client_for(handler)
    rows = run(client.get_all_pages("/me/library/songs", max_items=10))

    assert rows == [{"id": "1"}, {"id": "2"}]
    assert offsets == [0, 1]


def test_structured_response_uses_stable_shape():
    payload = structured_response(
        method="get",
        path="/catalog/us/search",
        params={"term": "stars", "l": None},
        payload={"results": {"songs": {"data": []}}, "meta": {"x": 1}},
    )

    assert payload["request"]["method"] == "GET"
    assert payload["request"]["params"] == {"term": "stars"}
    assert payload["results"] == {"songs": {"data": []}}
