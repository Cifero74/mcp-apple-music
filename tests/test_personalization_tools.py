import pytest

from tests.fakes import build_tools, run


def test_rating_tools_normalize_library_resource_types():
    tools, client = build_tools()

    run(tools["set_resource_rating"]("library", "songs", "i.abc", 1))

    assert client.calls[-1]["kind"] == "put"
    assert client.calls[-1]["path"] == "/me/ratings/library-songs/i.abc"
    assert client.calls[-1]["body"] == {"type": "ratings", "attributes": {"value": 1}}


def test_rating_value_is_validated_before_api_call():
    tools, client = build_tools()

    with pytest.raises(ValueError):
        run(tools["set_resource_rating"]("catalog", "songs", "123", 2))

    assert client.calls == []


def test_zero_rating_is_removed_with_delete_not_set():
    tools, client = build_tools()

    with pytest.raises(ValueError):
        run(tools["set_resource_rating"]("catalog", "songs", "123", 0))

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


def test_recently_played_stations_uses_radio_stations_endpoint():
    tools, client = build_tools()

    run(tools["get_recently_played_stations"]())

    assert client.calls[-1]["path"] == "/me/recent/radio-stations"


def test_favorites_write_uses_query_params_and_rejects_blank_ids():
    tools, client = build_tools()

    report = run(tools["add_resources_to_favorites"]("songs", "1,2"))

    assert client.calls[-1]["path"] == "/me/favorites"
    assert client.calls[-1]["params"] == {"ids[songs]": "1,2"}
    assert report["request"]["params"] == {"ids[songs]": "1,2"}

    with pytest.raises(ValueError):
        run(tools["add_resources_to_favorites"]("songs", ",,"))


def test_replay_uses_music_summaries_year_filter():
    tools, client = build_tools()

    run(tools["get_replay"](year="2025"))

    assert client.calls[-1]["path"] == "/me/music-summaries"
    assert client.calls[-1]["params"]["filter[year]"] == "2025"


def test_personalization_dynamic_path_segments_are_encoded():
    tools, client = build_tools()

    run(tools["get_resource_rating"]("catalog", "songs", "1/../?#frag"))
    run(tools["get_recommendation_relationship"]("rec/1", "contents?x=1"))

    assert client.calls[-2]["path"] == "/me/ratings/songs/1%2F..%2F%3F%23frag"
    assert client.calls[-1]["path"] == "/me/recommendations/rec%2F1/contents%3Fx%3D1"


def test_user_storefront_uses_user_auth():
    tools, client = build_tools()

    run(tools["get_user_storefront"]())

    assert client.calls[-1]["path"] == "/me/storefront"
    assert client.calls[-1]["user_auth"] is True
