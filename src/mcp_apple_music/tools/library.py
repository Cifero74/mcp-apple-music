"""Apple Music user-library tools."""

from __future__ import annotations

from typing import Any

from ..api_manifest import LIBRARY_RESOURCE_TYPES
from .common import (
    ClientGetter,
    csv_param,
    clamp,
    maybe_text,
    operation_report,
    paging_params,
    path_segment,
    require_values,
    typed_ids_params,
    validate_choice,
)

LIBRARY_CHOICES = tuple(LIBRARY_RESOURCE_TYPES)
ADDABLE_CATALOG_CHOICES = ("albums", "songs", "music-videos", "playlists")
LIBRARY_PATH_SEGMENTS = {
    "library-albums": "albums",
    "library-artists": "artists",
    "library-songs": "songs",
    "library-music-videos": "music-videos",
    "library-playlists": "playlists",
    "library-playlist-folders": "playlist-folders",
}


def _library_path(resource_type: str) -> str:
    resource = validate_choice(resource_type, LIBRARY_CHOICES, "resource_type")
    return path_segment(LIBRARY_PATH_SEGMENTS[resource], "resource_type")


def register_library_tools(mcp: Any, get_client: ClientGetter) -> None:
    @mcp.tool()
    async def get_library_resource(
        resource_type: str,
        resource_id: str,
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get one resource from the user's Apple Music library."""
        resource = validate_choice(resource_type, LIBRARY_CHOICES, "resource_type")
        path = f"/me/library/{_library_path(resource)}/{path_segment(resource_id, 'resource_id')}"
        payload = await get_client().request_structured(
            "GET",
            path,
            params={"include": csv_param(include)},
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Library {resource}")

    @mcp.tool()
    async def get_library_resources(
        resource_type: str,
        ids: str,
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get multiple library resources of one type by comma-separated IDs."""
        resource = validate_choice(resource_type, LIBRARY_CHOICES, "resource_type")
        payload = await get_client().request_structured(
            "GET",
            f"/me/library/{_library_path(resource)}",
            params={"ids": ids, "include": csv_param(include)},
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Library {resource}")

    @mcp.tool()
    async def get_library_resources_all(
        resource_type: str,
        limit: int = 25,
        offset: int = 0,
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """List a paginated collection from the user's Apple Music library."""
        resource = validate_choice(resource_type, LIBRARY_CHOICES, "resource_type")
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            include=csv_param(include),
        )
        payload = await get_client().request_structured(
            "GET",
            f"/me/library/{_library_path(resource)}",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Library {resource}")

    @mcp.tool()
    async def get_library_relationship(
        resource_type: str,
        resource_id: str,
        relationship: str,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Fetch a relationship for a library resource."""
        resource = validate_choice(resource_type, LIBRARY_CHOICES, "resource_type")
        path = (
            f"/me/library/{_library_path(resource)}/"
            f"{path_segment(resource_id, 'resource_id')}/"
            f"{path_segment(relationship, 'relationship')}"
        )
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured("GET", path, params=params, user_auth=True)
        return maybe_text(payload, format, title=f"Library {resource} {relationship}")

    @mcp.tool()
    async def get_library_songs(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Compatibility wrapper for listing library songs."""
        return await get_library_resources_all("library-songs", limit, offset, format=format)

    @mcp.tool()
    async def get_library_albums(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Compatibility wrapper for listing library albums."""
        return await get_library_resources_all("library-albums", limit, offset, format=format)

    @mcp.tool()
    async def get_library_artists(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Compatibility wrapper for listing library artists."""
        return await get_library_resources_all("library-artists", limit, offset, format=format)

    @mcp.tool()
    async def get_library_playlists(
        limit: int = 100,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Compatibility wrapper for listing library playlists."""
        return await get_library_resources_all("library-playlists", limit, offset, format=format)

    @mcp.tool()
    async def get_playlist_tracks(
        playlist_id: str,
        limit: int = 100,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get tracks inside a library playlist."""
        path = f"/me/library/playlists/{path_segment(playlist_id, 'playlist_id')}/tracks"
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured("GET", path, params=params, user_auth=True)
        return maybe_text(payload, format, title=f"Playlist {playlist_id} tracks")

    @mcp.tool()
    async def add_resources_to_library(
        resource_type: str,
        ids: str,
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Add catalog albums, songs, music videos, or playlists to the user's library."""
        resource = validate_choice(resource_type, ADDABLE_CATALOG_CHOICES, "resource_type")
        path = "/me/library"
        attempted = require_values(ids, "ids")
        size = clamp(batch_size, 1, 100)
        batches = [attempted[index : index + size] for index in range(0, len(attempted), size)]
        params_list = [{f"ids[{resource}]": ",".join(batch)} for batch in batches]
        batch_preview = [{"params": params} for params in params_list]
        if dry_run:
            return {
                **operation_report(
                    operation="add_resources_to_library",
                    path=path,
                    attempted_ids=attempted,
                    dry_run=True,
                    request_params=params_list[0] if len(params_list) == 1 else None,
                    request_body={"batches": batch_preview} if len(params_list) > 1 else None,
                ),
                "batch_size": size,
                "batch_count": len(batches),
            }
        outcomes = await get_client().post_many_outcomes(
            path,
            [None] * len(params_list),
            params_list,
        )
        return {
            **operation_report(
                operation="add_resources_to_library",
                path=path,
                attempted_ids=attempted,
                request_params=params_list[0] if len(params_list) == 1 else None,
                batch_outcomes=outcomes,
                responses=[outcome["response"] for outcome in outcomes if outcome["success"]],
            ),
            "batch_size": size,
            "batch_count": len(batches),
        }

    @mcp.tool()
    async def get_root_library_playlist_folder(
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get the root folder of the user's library playlists."""
        payload = await get_client().request_structured(
            "GET",
            "/me/library/playlist-folders/root",
            params={"include": csv_param(include)},
            user_auth=True,
        )
        return maybe_text(payload, format, title="Root playlist folder")

    @mcp.tool()
    async def get_library_playlist_folder(
        folder_id: str,
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get a library playlist folder by ID."""
        payload = await get_client().request_structured(
            "GET",
            f"/me/library/playlist-folders/{path_segment(folder_id, 'folder_id')}",
            params={"include": csv_param(include)},
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Playlist folder {folder_id}")

    @mcp.tool()
    async def get_multiple_library_resources(
        typed_ids: str,
        include: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get multiple library resources by typed IDs such as library-songs:i.x."""
        params = {
            **typed_ids_params(typed_ids, choices=LIBRARY_CHOICES),
            "include": csv_param(include),
        }
        payload = await get_client().request_structured(
            "GET",
            "/me/library",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Library resources")
