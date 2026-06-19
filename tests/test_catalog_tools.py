import pytest

from tests.fakes import build_tools, run


def test_catalog_resource_uses_storefront_and_catalog_auth():
    tools, client = build_tools()

    payload = run(tools["get_catalog_resource"]("songs", "123", include="albums,artists"))

    assert payload["request"]["path"] == "/catalog/us/songs/123"
    assert client.calls[-1]["user_auth"] is False
    assert client.calls[-1]["params"]["include"] == "albums,artists"


def test_catalog_filter_validates_upc_and_isrc_shapes():
    tools, client = build_tools()

    run(tools["get_catalog_resources_by_filter"]("songs", "isrc", "USRC17607839"))

    assert client.calls[-1]["path"] == "/catalog/us/songs"
    assert client.calls[-1]["params"]["filter[isrc]"] == "USRC17607839"

    with pytest.raises(ValueError):
        run(tools["get_catalog_resources_by_filter"]("albums", "isrc", "bad"))


def test_catalog_relationship_and_view_paths_are_structured():
    tools, client = build_tools()

    run(tools["get_catalog_relationship"]("artists", "42", "albums", limit=10, offset=5))
    assert client.calls[-1]["path"] == "/catalog/us/artists/42/albums"
    assert client.calls[-1]["params"] == {"limit": 10, "offset": 5}

    run(tools["get_catalog_view"]("record-labels", "label", "latest-releases"))
    assert client.calls[-1]["path"] == "/catalog/us/record-labels/label/view/latest-releases"


def test_catalog_text_format_is_available():
    tools, _client = build_tools()

    text = run(tools["get_catalog_resource"]("songs", "123", format="text"))

    assert "Catalog songs" in text
    assert "songs:1" in text
