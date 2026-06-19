import pytest

from mcp_apple_music.tools import register_tools
from tests.fakes import FakeClient, FakeMCP, build_tools, run


def test_library_collection_wrapper_uses_generic_library_endpoint():
    tools, client = build_tools()

    payload = run(tools["get_library_songs"](limit=7, offset=2))

    assert payload["request"]["path"] == "/me/library/songs"
    assert client.calls[-1]["user_auth"] is True
    assert client.calls[-1]["params"] == {"limit": 7, "offset": 2}


def test_add_resources_to_library_supports_dry_run():
    tools, client = build_tools()

    report = run(tools["add_resources_to_library"]("songs", "1,2", dry_run=True))

    assert report["dry_run"] is True
    assert report["request"]["path"] == "/me/library"
    assert report["request"]["params"] == {"ids[songs]": "1,2"}
    assert client.calls == []


def test_add_resources_to_library_rejects_blank_ids_before_api_call():
    tools, client = build_tools()

    with pytest.raises(ValueError):
        run(tools["add_resources_to_library"]("songs", ", ,,"))

    assert client.calls == []


def test_create_playlist_can_preview_tracks_and_parent_folder():
    tools, _client = build_tools()

    report = run(
        tools["create_playlist"](
            "Road Trip",
            description="for 2008 scrobbles",
            track_ids=["a", "b"],
            track_type="songs",
            parent_folder_id="folder.1",
            dry_run=True,
        )
    )

    assert report["dry_run"] is True
    body = report["request"]["body"]
    assert body["attributes"]["name"] == "Road Trip"
    assert body["relationships"]["tracks"]["data"][0] == {"id": "a", "type": "songs"}
    assert body["relationships"]["parent"]["data"][0] == {
        "id": "folder.1",
        "type": "library-playlist-folders",
    }


def test_add_tracks_batches_requests():
    tools, client = build_tools()

    report = run(
        tools["add_tracks_to_playlist"](
            "p.1",
            ["1", "2", "3"],
            track_type="library-songs",
            batch_size=2,
        )
    )

    assert report["batch_count"] == 2
    assert [call["kind"] for call in client.calls] == ["post", "post"]
    assert client.calls[0]["path"] == "/me/library/playlists/p.1/tracks"
    assert client.calls[0]["body"]["data"] == [
        {"id": "1", "type": "library-songs"},
        {"id": "2", "type": "library-songs"},
    ]


def test_add_tracks_reports_partial_batch_failure():
    class PartialFailureClient(FakeClient):
        async def post_many_outcomes(self, path, bodies, params_list=None):
            return [
                {
                    "batch_index": 0,
                    "success": True,
                    "status_code": 202,
                    "request": {"method": "POST", "path": path, "params": {}, "body": bodies[0]},
                    "attempted": {"count": 2, "ids": ["1", "2"]},
                    "response": {},
                },
                {
                    "batch_index": 1,
                    "success": False,
                    "status_code": 429,
                    "request": {"method": "POST", "path": path, "params": {}, "body": bodies[1]},
                    "attempted": {"count": 1, "ids": ["3"]},
                    "error": {"message": "Rate limited", "body": {"errors": []}},
                },
            ]

    fake_mcp = FakeMCP()
    client = PartialFailureClient()
    register_tools(fake_mcp, lambda: client)

    report = run(
        fake_mcp.tools["add_tracks_to_playlist"](
            "p.1",
            ["1", "2", "3", "4"],
            batch_size=2,
        )
    )

    assert report["status"] == "partial_failure"
    assert report["succeeded"]["ids"] == ["1", "2"]
    assert report["failed"]["ids"] == ["3"]
    assert report["pending"]["ids"] == ["4"]
    assert "retry only failed and pending IDs" in report["next_action"]


def test_dynamic_library_path_segments_are_encoded():
    tools, client = build_tools()

    run(tools["get_playlist_tracks"]("p/../?#frag"))

    assert client.calls[-1]["path"] == "/me/library/playlists/p%2F..%2F%3F%23frag/tracks"


def test_get_multiple_library_resources_uses_resource_typed_params():
    tools, client = build_tools()

    run(tools["get_multiple_library_resources"]("library-songs:i.1,library-albums:l.2"))

    assert client.calls[-1]["params"] == {
        "ids[library-songs]": "i.1",
        "ids[library-albums]": "l.2",
        "include": None,
    }
