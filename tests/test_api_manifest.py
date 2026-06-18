from mcp_apple_music.api_manifest import (
    CATALOG_RESOURCE_TYPES,
    EXPECTED_CATEGORIES,
    LIBRARY_RESOURCE_TYPES,
    all_endpoints,
    coverage_summary,
    endpoint_tool_map,
    endpoint_keys,
    get_endpoint,
    tool_for_endpoint,
)
from mcp_apple_music.tools import TOOL_NAMES, register_tools

from tests.fakes import FakeClient, FakeMCP


def test_manifest_covers_expected_categories():
    summary = coverage_summary()

    assert set(summary) == EXPECTED_CATEGORIES
    assert all(count > 0 for count in summary.values())


def test_manifest_has_unique_stable_keys():
    keys = [endpoint.key for endpoint in all_endpoints()]

    assert len(keys) == len(set(keys))
    assert endpoint_keys() == frozenset(keys)


def test_manifest_includes_documented_resource_families():
    catalog = get_endpoint("catalog_resource_get")
    library = get_endpoint("library_resource_get")

    assert set(CATALOG_RESOURCE_TYPES).issubset(catalog.resource_types)
    assert set(LIBRARY_RESOURCE_TYPES).issubset(library.resource_types)


def test_manifest_marks_side_effects_and_auth_modes():
    assert get_endpoint("library_playlist_create").side_effect is True
    assert get_endpoint("library_playlist_create").auth == "user"
    assert get_endpoint("search_catalog").auth == "catalog"
    assert get_endpoint("ratings_catalog_delete").method == "DELETE"
    assert get_endpoint("ratings_catalog_add").method == "PUT"


def test_manifest_endpoint_tools_exist_in_registry():
    missing = {
        endpoint.key: tool_for_endpoint(endpoint)
        for endpoint in all_endpoints()
        if not tool_for_endpoint(endpoint) or tool_for_endpoint(endpoint) not in TOOL_NAMES
    }

    assert missing == {}
    assert set(endpoint_tool_map()) == endpoint_keys()


def test_register_tools_exposes_declared_tools():
    fake_mcp = FakeMCP()
    client = FakeClient()

    register_tools(fake_mcp, lambda: client)

    assert TOOL_NAMES.issubset(fake_mcp.tools)
