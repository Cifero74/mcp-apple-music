"""Apple Music API coverage manifest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AuthMode = Literal["catalog", "user"]
HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


@dataclass(frozen=True)
class Endpoint:
    key: str
    category: str
    title: str
    method: HttpMethod
    path: str
    auth: AuthMode
    parameters: tuple[str, ...] = ()
    resource_types: tuple[str, ...] = ()
    side_effect: bool = False
    tool: str | None = None
    unsupported_note: str | None = None


CATALOG_RESOURCE_TYPES = (
    "albums",
    "artists",
    "songs",
    "music-videos",
    "playlists",
    "stations",
    "station-genres",
    "activities",
    "curators",
    "apple-curators",
    "record-labels",
    "genres",
)

LIBRARY_RESOURCE_TYPES = (
    "library-albums",
    "library-artists",
    "library-songs",
    "library-music-videos",
    "library-playlists",
    "library-playlist-folders",
)

RATING_CATALOG_TYPES = ("albums", "music-videos", "playlists", "songs", "stations")
RATING_LIBRARY_TYPES = ("library-albums", "library-music-videos", "library-playlists", "library-songs")


ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint("catalog_resource_get", "catalog", "Get one catalog resource", "GET", "/catalog/{storefront}/{resource_type}/{id}", "catalog", ("storefront", "resource_type", "id", "l", "include"), CATALOG_RESOURCE_TYPES),
    Endpoint("catalog_resource_multiple", "catalog", "Get multiple catalog resources", "GET", "/catalog/{storefront}/{resource_type}", "catalog", ("storefront", "resource_type", "ids", "l", "include"), CATALOG_RESOURCE_TYPES),
    Endpoint("catalog_resource_relationship", "catalog", "Get catalog resource relationship", "GET", "/catalog/{storefront}/{resource_type}/{id}/{relationship}", "catalog", ("storefront", "resource_type", "id", "relationship", "l", "limit", "offset"), CATALOG_RESOURCE_TYPES),
    Endpoint("catalog_resource_view", "catalog", "Get catalog resource relationship view", "GET", "/catalog/{storefront}/{resource_type}/{id}/view/{view}", "catalog", ("storefront", "resource_type", "id", "view", "l", "limit", "offset"), ("albums", "artists", "music-videos", "playlists", "record-labels")),
    Endpoint("catalog_albums_by_upc", "catalog", "Get multiple catalog albums by UPC", "GET", "/catalog/{storefront}/albums", "catalog", ("storefront", "filter[upc]", "l", "include"), ("albums",)),
    Endpoint("catalog_songs_by_isrc", "catalog", "Get multiple catalog songs by ISRC", "GET", "/catalog/{storefront}/songs", "catalog", ("storefront", "filter[isrc]", "l", "include"), ("songs",)),
    Endpoint("catalog_music_videos_by_isrc", "catalog", "Get multiple catalog music videos by ISRC", "GET", "/catalog/{storefront}/music-videos", "catalog", ("storefront", "filter[isrc]", "l", "include"), ("music-videos",)),
    Endpoint("catalog_equivalent_ids", "catalog", "Get equivalent catalog IDs", "GET", "/catalog/{storefront}/{resource_type}/{id}/equivalents", "catalog", ("storefront", "resource_type", "id", "l"), ("albums", "songs", "music-videos")),
    Endpoint("catalog_charts_playlists", "playlists", "Get charts playlists by storefront", "GET", "/catalog/{storefront}/playlists/charts", "catalog", ("storefront", "l", "limit", "offset"), ("playlists",)),
    Endpoint("catalog_live_radio_stations", "stations", "Get Apple Music live radio stations", "GET", "/catalog/{storefront}/stations", "catalog", ("storefront", "filter[featured]", "l", "limit", "offset"), ("stations",)),
    Endpoint("catalog_personal_station", "stations", "Get user's personal Apple Music station", "GET", "/me/stations", "user", ("limit", "offset"), ("stations",)),
    Endpoint("catalog_station_genres_all", "stations", "Get all station genres", "GET", "/catalog/{storefront}/station-genres", "catalog", ("storefront", "l", "limit", "offset"), ("station-genres",)),
    Endpoint("search_catalog", "search", "Search for catalog resources", "GET", "/catalog/{storefront}/search", "catalog", ("storefront", "term", "types", "l", "limit", "offset"), CATALOG_RESOURCE_TYPES, tool="search_catalog"),
    Endpoint("search_catalog_hints", "search", "Get catalog search hints", "GET", "/catalog/{storefront}/search/hints", "catalog", ("storefront", "term", "types", "l", "limit"), CATALOG_RESOURCE_TYPES),
    Endpoint("search_catalog_suggestions", "search", "Get catalog search suggestions", "GET", "/catalog/{storefront}/search/suggestions", "catalog", ("storefront", "term", "types", "l", "limit"), CATALOG_RESOURCE_TYPES),
    Endpoint("search_library", "search", "Search for library resources", "GET", "/me/library/search", "user", ("term", "types", "limit", "offset"), LIBRARY_RESOURCE_TYPES, tool="search_library"),
    Endpoint("library_resource_get", "library", "Get one library resource", "GET", "/me/library/{resource_type}/{id}", "user", ("resource_type", "id", "include"), LIBRARY_RESOURCE_TYPES),
    Endpoint("library_resource_multiple", "library", "Get multiple library resources", "GET", "/me/library/{resource_type}", "user", ("resource_type", "ids", "include"), LIBRARY_RESOURCE_TYPES),
    Endpoint("library_resource_all", "library", "Get all library resources", "GET", "/me/library/{resource_type}", "user", ("resource_type", "limit", "offset"), LIBRARY_RESOURCE_TYPES),
    Endpoint("library_resource_relationship", "library", "Get library resource relationship", "GET", "/me/library/{resource_type}/{id}/{relationship}", "user", ("resource_type", "id", "relationship", "limit", "offset"), LIBRARY_RESOURCE_TYPES),
    Endpoint("library_add_resource", "library", "Add a resource to a library", "POST", "/me/library", "user", ("resource_type", "ids"), ("albums", "songs", "music-videos", "playlists"), True),
    Endpoint("library_playlist_folder_root", "playlists", "Get root library playlists folder", "GET", "/me/library/playlist-folders/root", "user", ("include",), ("library-playlist-folders",)),
    Endpoint("library_playlist_folder_create", "playlists", "Create a new library playlist folder", "POST", "/me/library/playlist-folders", "user", ("name", "parent_id"), ("library-playlist-folders",), True),
    Endpoint("library_playlist_create", "playlists", "Create a new library playlist", "POST", "/me/library/playlists", "user", ("name", "description", "tracks", "parent_id"), ("library-playlists",), True, "create_playlist"),
    Endpoint("library_playlist_add_tracks", "playlists", "Add tracks to a library playlist", "POST", "/me/library/playlists/{playlist_id}/tracks", "user", ("playlist_id", "track_ids", "track_type"), ("songs", "library-songs"), True, "add_tracks_to_playlist"),
    Endpoint("ratings_catalog_get", "ratings", "Get personal catalog content ratings", "GET", "/me/ratings/{resource_type}/{id}", "user", ("resource_type", "id"), RATING_CATALOG_TYPES),
    Endpoint("ratings_catalog_multiple", "ratings", "Get multiple personal catalog content ratings", "GET", "/me/ratings/{resource_type}", "user", ("resource_type", "ids"), RATING_CATALOG_TYPES),
    Endpoint("ratings_catalog_add", "ratings", "Add personal catalog content rating", "PUT", "/me/ratings/{resource_type}/{id}", "user", ("resource_type", "id", "rating"), RATING_CATALOG_TYPES, True),
    Endpoint("ratings_catalog_delete", "ratings", "Delete personal catalog content rating", "DELETE", "/me/ratings/{resource_type}/{id}", "user", ("resource_type", "id"), RATING_CATALOG_TYPES, True),
    Endpoint("ratings_library_get", "ratings", "Get personal library content ratings", "GET", "/me/ratings/library-{resource_type}/{id}", "user", ("resource_type", "id"), RATING_LIBRARY_TYPES),
    Endpoint("ratings_library_multiple", "ratings", "Get multiple personal library content ratings", "GET", "/me/ratings/library-{resource_type}", "user", ("resource_type", "ids"), RATING_LIBRARY_TYPES),
    Endpoint("ratings_library_add", "ratings", "Add personal library content rating", "PUT", "/me/ratings/library-{resource_type}/{id}", "user", ("resource_type", "id", "rating"), RATING_LIBRARY_TYPES, True),
    Endpoint("ratings_library_delete", "ratings", "Delete personal library content rating", "DELETE", "/me/ratings/library-{resource_type}/{id}", "user", ("resource_type", "id"), RATING_LIBRARY_TYPES, True),
    Endpoint("genres_catalog_get", "genres_charts", "Get a catalog genre", "GET", "/catalog/{storefront}/genres/{id}", "catalog", ("storefront", "id", "l"), ("genres",)),
    Endpoint("genres_catalog_multiple", "genres_charts", "Get multiple catalog genres", "GET", "/catalog/{storefront}/genres", "catalog", ("storefront", "ids", "l"), ("genres",)),
    Endpoint("genres_catalog_all", "genres_charts", "Get catalog top charts genres", "GET", "/catalog/{storefront}/genres", "catalog", ("storefront", "l", "limit", "offset"), ("genres",)),
    Endpoint("charts_catalog", "genres_charts", "Get catalog charts", "GET", "/catalog/{storefront}/charts", "catalog", ("storefront", "types", "chart", "genre", "l", "limit", "offset")),
    Endpoint("favorites_add_resource", "favorites", "Add resource to favorites", "POST", "/me/favorites", "user", ("resource_type", "ids"), CATALOG_RESOURCE_TYPES + LIBRARY_RESOURCE_TYPES, True),
    Endpoint("replay_user_data", "replay", "Get user's replay data", "GET", "/me/replay", "user", ("period", "l", "limit", "offset")),
    Endpoint("recommendations_get", "recommendations", "Get a recommendation", "GET", "/me/recommendations/{id}", "user", ("id", "include", "limit", "offset")),
    Endpoint("recommendations_relationship", "recommendations", "Get recommendation relationship", "GET", "/me/recommendations/{id}/{relationship}", "user", ("id", "relationship", "limit", "offset")),
    Endpoint("recommendations_multiple", "recommendations", "Get multiple recommendations", "GET", "/me/recommendations", "user", ("ids", "include")),
    Endpoint("recommendations_default", "recommendations", "Get default recommendations", "GET", "/me/recommendations", "user", ("limit", "offset"), tool="get_recommendations"),
    Endpoint("history_heavy_rotation", "history", "Get heavy rotation content", "GET", "/me/history/heavy-rotation", "user", ("limit", "offset")),
    Endpoint("history_recently_played_resources", "history", "Get recently played resources", "GET", "/me/recent/played", "user", ("limit", "offset"), tool="get_recently_played"),
    Endpoint("history_recently_played_tracks", "history", "Get recently played tracks", "GET", "/me/recent/played/tracks", "user", ("limit", "offset")),
    Endpoint("history_recently_played_stations", "history", "Get recently played stations", "GET", "/me/recent/played/stations", "user", ("limit", "offset")),
    Endpoint("history_recently_added_resources", "history", "Get recently added resources", "GET", "/me/library/recently-added", "user", ("limit", "offset")),
    Endpoint("multi_resource_catalog_typed_ids", "multi_resource", "Get multiple catalog resources by typed IDs", "GET", "/catalog/{storefront}", "catalog", ("storefront", "ids", "l", "include"), CATALOG_RESOURCE_TYPES),
    Endpoint("multi_resource_library_typed_ids", "multi_resource", "Get multiple library resources by typed IDs", "GET", "/me/library", "user", ("ids", "include"), LIBRARY_RESOURCE_TYPES),
    Endpoint("essentials_user_storefront", "essentials", "Get a user's storefront", "GET", "/me/storefront", "user", tool="get_user_storefront"),
    Endpoint("essentials_connectivity_test", "essentials", "Placeholder endpoint to test connectivity", "GET", "/test", "catalog"),
)

EXPECTED_CATEGORIES = frozenset(
    {
        "catalog",
        "playlists",
        "stations",
        "search",
        "library",
        "ratings",
        "genres_charts",
        "favorites",
        "replay",
        "recommendations",
        "history",
        "multi_resource",
        "essentials",
    }
)

ENDPOINT_TOOL_MAP = {
    "catalog_resource_get": "get_catalog_resource",
    "catalog_resource_multiple": "get_catalog_resources",
    "catalog_resource_relationship": "get_catalog_relationship",
    "catalog_resource_view": "get_catalog_view",
    "catalog_albums_by_upc": "get_catalog_resources_by_filter",
    "catalog_songs_by_isrc": "get_catalog_resources_by_filter",
    "catalog_music_videos_by_isrc": "get_catalog_resources_by_filter",
    "catalog_equivalent_ids": "get_equivalent_catalog_ids",
    "catalog_charts_playlists": "get_catalog_playlist_charts",
    "catalog_live_radio_stations": "get_live_radio_stations",
    "catalog_personal_station": "get_personal_station",
    "catalog_station_genres_all": "get_station_genres",
    "search_catalog": "search_catalog",
    "search_catalog_hints": "get_catalog_search_hints",
    "search_catalog_suggestions": "get_catalog_search_suggestions",
    "search_library": "search_library",
    "library_resource_get": "get_library_resource",
    "library_resource_multiple": "get_library_resources",
    "library_resource_all": "get_library_resources_all",
    "library_resource_relationship": "get_library_relationship",
    "library_add_resource": "add_resources_to_library",
    "library_playlist_folder_root": "get_root_library_playlist_folder",
    "library_playlist_folder_create": "create_playlist_folder",
    "library_playlist_create": "create_playlist",
    "library_playlist_add_tracks": "add_tracks_to_playlist",
    "ratings_catalog_get": "get_resource_rating",
    "ratings_catalog_multiple": "get_resource_ratings",
    "ratings_catalog_add": "set_resource_rating",
    "ratings_catalog_delete": "delete_resource_rating",
    "ratings_library_get": "get_resource_rating",
    "ratings_library_multiple": "get_resource_ratings",
    "ratings_library_add": "set_resource_rating",
    "ratings_library_delete": "delete_resource_rating",
    "genres_catalog_get": "get_catalog_resource",
    "genres_catalog_multiple": "get_catalog_resources",
    "genres_catalog_all": "get_catalog_genres",
    "charts_catalog": "get_catalog_charts",
    "favorites_add_resource": "add_resources_to_favorites",
    "replay_user_data": "get_replay",
    "recommendations_get": "get_recommendation",
    "recommendations_relationship": "get_recommendation_relationship",
    "recommendations_multiple": "get_recommendations",
    "recommendations_default": "get_recommendations",
    "history_heavy_rotation": "get_heavy_rotation",
    "history_recently_played_resources": "get_recently_played",
    "history_recently_played_tracks": "get_recently_played_tracks",
    "history_recently_played_stations": "get_recently_played_stations",
    "history_recently_added_resources": "get_recently_added_resources",
    "multi_resource_catalog_typed_ids": "get_multiple_catalog_resources",
    "multi_resource_library_typed_ids": "get_multiple_library_resources",
    "essentials_user_storefront": "get_user_storefront",
    "essentials_connectivity_test": "test_apple_music_api_connectivity",
}


def all_endpoints() -> tuple[Endpoint, ...]:
    return ENDPOINTS


def endpoint_keys() -> frozenset[str]:
    return frozenset(endpoint.key for endpoint in ENDPOINTS)


def endpoints_by_category(category: str) -> tuple[Endpoint, ...]:
    return tuple(endpoint for endpoint in ENDPOINTS if endpoint.category == category)


def get_endpoint(key: str) -> Endpoint:
    for endpoint in ENDPOINTS:
        if endpoint.key == key:
            return endpoint
    raise KeyError(key)


def coverage_summary() -> dict[str, int]:
    return {category: len(endpoints_by_category(category)) for category in sorted(EXPECTED_CATEGORIES)}


def tool_for_endpoint(endpoint: Endpoint) -> str | None:
    return endpoint.tool or ENDPOINT_TOOL_MAP.get(endpoint.key)


def endpoint_tool_map() -> dict[str, str]:
    return {endpoint.key: tool for endpoint in ENDPOINTS if (tool := tool_for_endpoint(endpoint))}
