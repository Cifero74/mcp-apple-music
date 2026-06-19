# Apple Music API Coverage

This fork keeps endpoint coverage explicit in `src/mcp_apple_music/api_manifest.py`.
Every manifest endpoint maps to a registered MCP tool through `ENDPOINT_TOOL_MAP`,
and `tests/test_api_manifest.py` fails if a manifest entry has no tool.

## Tool Surface

| Area | Tools |
| --- | --- |
| Catalog resources | `get_catalog_resource`, `get_catalog_resources`, `get_catalog_relationship`, `get_catalog_view`, `get_multiple_catalog_resources` |
| Special catalog lookups | `get_catalog_resources_by_filter`, `get_equivalent_catalog_ids` |
| Search | `search_catalog`, `get_catalog_search_hints`, `get_catalog_search_suggestions`, `search_library` |
| Genres, charts, stations | `get_catalog_genres`, `get_catalog_charts`, `get_catalog_playlist_charts`, `get_station_genres`, `get_live_radio_stations`, `get_personal_station` |
| Library resources | `get_library_resource`, `get_library_resources`, `get_library_resources_all`, `get_library_relationship`, `get_multiple_library_resources` |
| Compatibility library aliases | `get_library_songs`, `get_library_albums`, `get_library_artists`, `get_library_playlists`, `get_playlist_tracks` |
| Library writes | `add_resources_to_library`, `create_playlist`, `add_tracks_to_playlist`, `create_playlist_folder` |
| Playlist folders | `get_root_library_playlist_folder`, `get_library_playlist_folder`, `create_playlist_folder` |
| Ratings | `get_resource_rating`, `get_resource_ratings`, `set_resource_rating`, `delete_resource_rating` |
| Favorites | `add_resources_to_favorites` |
| Replay and recommendations | `get_replay`, `get_recommendations`, `get_recommendation`, `get_recommendation_relationship` |
| History | `get_heavy_rotation`, `get_recently_played`, `get_recently_played_tracks`, `get_recently_played_stations`, `get_recently_added_resources` |
| Essentials | `get_user_storefront`, `test_apple_music_api_connectivity` |

## Resource Families

Catalog tools cover albums, artists, songs, music videos, playlists, stations,
station genres, activities, curators, Apple curators, record labels, and genres.
Library tools cover library albums, artists, songs, music videos, playlists, and
playlist folders.

## Structured Responses

Read tools return structured dictionaries by default:

```json
{
  "request": {
    "method": "GET",
    "path": "/catalog/us/songs/123",
    "params": {}
  },
  "data": [],
  "results": {},
  "meta": {},
  "next": null,
  "raw": {}
}
```

Most read tools accept `format="text"` for compact human-readable summaries.
Side-effect tools return operation reports with the attempted IDs, canonical
request path/params/body, dry-run status, accepted API responses, batching
metadata, and explicit `succeeded`, `failed`, and `pending` ID groups when a
later batch fails.

## Side Effects

The write surface is intentionally explicit:

- `create_playlist` supports `dry_run`, optional initial tracks, and optional parent playlist folder.
- `add_tracks_to_playlist` supports `dry_run` and batches requests at up to 100 tracks. If a later batch fails, the report preserves earlier successes and tells callers to retry only failed and pending IDs.
- `create_playlist_folder` supports `dry_run`.
- `add_resources_to_library` and `add_resources_to_favorites` use Apple's `ids[{resource_type}]` query parameters and reject blank ID input before sending a request.
- `set_resource_rating` writes only documented like/dislike values (`1` or `-1`); use `delete_resource_rating` to remove a rating.

Apple's REST API does not expose playlist reordering, playlist deletion, or
remove-track-from-playlist operations in this manifest snapshot. Those remain
outside the MCP surface rather than being simulated locally.

## Last.fm Workflow Shape

Use the Last.fm exporter as a candidate source, then let an agent use this MCP
for Apple Music matching and playlist writes:

1. Query local Last.fm history for a period, such as 2008.
2. Search Apple Music with `search_catalog` or `get_catalog_search_hints`.
3. Resolve catalog song IDs, using ISRC when available through `get_catalog_resources_by_filter`.
4. Preview playlist creation with `create_playlist(..., dry_run=True)`.
5. Add tracks with `add_tracks_to_playlist`, batching and inspecting the returned operation report.
