import pytest

from tests.fakes import build_tools, run


def test_rating_tools_normalize_library_resource_types():
    tools, client = build_tools()

    run(tools["set_resource_rating"]("library", "songs", "i.abc", 1))

    assert client.calls[-1]["kind"] == "put"
    assert client.calls[-1]["path"] == "/me/ratings/library-songs/i.abc"
    assert client.calls[-1]["body"] == {"attributes": {"value": 1}}


def test_rating_value_is_validated_before_api_call():
    tools, client = build_tools()

    with pytest.raises(ValueError):
        run(tools["set_resource_rating"]("catalog", "songs", "123", 2))

    assert client.calls == []


def test_delete_rating_reports_delete_method():
    tools, client = build_tools()

    report = run(tools["delete_resource_rating"]("catalog", "songs", "123"))

    assert client.calls[-1]["kind"] == "delete"
    assert report["request"]["method"] == "DELETE"
    assert report["attempted"]["ids"] == ["123"]


def test_recently_played_tracks_is_distinct_from_resources():
    tools, client = build_tools()

    run(tools["get_recently_played"]())
    run(tools["get_recently_played_tracks"]())

    assert client.calls[-2]["path"] == "/me/recent/played"
    assert client.calls[-1]["path"] == "/me/recent/played/tracks"


def test_user_storefront_uses_user_auth():
    tools, client = build_tools()

    run(tools["get_user_storefront"]())

    assert client.calls[-1]["path"] == "/me/storefront"
    assert client.calls[-1]["user_auth"] is True
