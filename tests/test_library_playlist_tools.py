from tests.fakes import build_tools, run


def test_library_collection_wrapper_uses_generic_library_endpoint():
    tools, client = build_tools()

    payload = run(tools["get_library_songs"](limit=7, offset=2))

    assert payload["request"]["path"] == "/me/library/library-songs"
    assert client.calls[-1]["user_auth"] is True
    assert client.calls[-1]["params"] == {"limit": 7, "offset": 2}


def test_add_resources_to_library_supports_dry_run():
    tools, client = build_tools()

    report = run(tools["add_resources_to_library"]("songs", "1,2", dry_run=True))

    assert report["dry_run"] is True
    assert report["request"]["path"] == "/me/library"
    assert report["request"]["body"]["data"] == [
        {"id": "1", "type": "songs"},
        {"id": "2", "type": "songs"},
    ]
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
