"""Tool registration for the Apple Music MCP server."""

from __future__ import annotations

from typing import Any

from .catalog import register_catalog_tools
from .common import ClientGetter
from .library import register_library_tools
from .personalization import register_personalization_tools
from .playlists import register_playlist_tools
from .search import register_search_tools

TOOL_NAMES = frozenset(
    {
        "add_resources_to_favorites",
        "add_resources_to_library",
        "add_tracks_to_playlist",
        "create_playlist",
        "create_playlist_folder",
        "delete_resource_rating",
        "get_catalog_charts",
        "get_catalog_genres",
        "get_catalog_playlist_charts",
        "get_catalog_relationship",
        "get_catalog_resource",
        "get_catalog_resources",
        "get_catalog_resources_by_filter",
        "get_catalog_search_hints",
        "get_catalog_search_suggestions",
        "get_catalog_view",
        "get_equivalent_catalog_ids",
        "get_heavy_rotation",
        "get_library_albums",
        "get_library_artists",
        "get_library_playlist_folder",
        "get_library_playlists",
        "get_library_relationship",
        "get_library_resource",
        "get_library_resources",
        "get_library_resources_all",
        "get_library_songs",
        "get_live_radio_stations",
        "get_multiple_catalog_resources",
        "get_multiple_library_resources",
        "get_personal_station",
        "get_playlist_tracks",
        "get_recently_added_resources",
        "get_recently_played",
        "get_recently_played_stations",
        "get_recently_played_tracks",
        "get_recommendation",
        "get_recommendation_relationship",
        "get_recommendations",
        "get_replay",
        "get_resource_rating",
        "get_resource_ratings",
        "get_root_library_playlist_folder",
        "get_station_genres",
        "get_user_storefront",
        "search_catalog",
        "search_library",
        "set_resource_rating",
        "test_apple_music_api_connectivity",
    }
)


def register_tools(mcp: Any, get_client: ClientGetter) -> None:
    register_search_tools(mcp, get_client)
    register_catalog_tools(mcp, get_client)
    register_library_tools(mcp, get_client)
    register_playlist_tools(mcp, get_client)
    register_personalization_tools(mcp, get_client)
