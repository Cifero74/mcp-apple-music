"""Apple Music user-library tools."""

from __future__ import annotations

from typing import Any

from ..api_manifest import LIBRARY_RESOURCE_TYPES
from .common import (
    ClientGetter,
    csv_param,
    maybe_text,
    operation_report,
    paging_params,
    relationship_body,
    validate_choice,
)

LIBRARY_CHOICES = tuple(LIBRARY_RESOURCE_TYPES)
ADDABLE_CATALOG_CHOICES = ("albums", "songs", "music-videos", "playlists")


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
        path = f"/me/library/{resource}/{resource_id}"
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
            f"/me/library/{resource}",
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
            f"/me/library/{resource}",
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
        path = f"/me/library/{resource}/{resource_id}/{relationship}"
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
        path = f"/me/library/playlists/{playlist_id}/tracks"
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured("GET", path, params=params, user_auth=True)
        return maybe_text(payload, format, title=f"Playlist {playlist_id} tracks")

    @mcp.tool()
    async def add_resources_to_library(
        resource_type: str,
        ids: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Add catalog albums, songs, music videos, or playlists to the user's library."""
        resource = validate_choice(resource_type, ADDABLE_CATALOG_CHOICES, "resource_type")
        path = "/me/library"
        body = relationship_body(ids, resource)
        attempted = [item["id"] for item in body["data"]]
        if dry_run:
            return operation_report(
                operation="add_resources_to_library",
                path=path,
                attempted_ids=attempted,
                dry_run=True,
                request_body=body,
            )
        response = await get_client().post(path, body)
        return operation_report(
            operation="add_resources_to_library",
            path=path,
            attempted_ids=attempted,
            request_body=body,
            responses=[response],
        )

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
            f"/me/library/playlist-folders/{folder_id}",
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
        payload = await get_client().request_structured(
            "GET",
            "/me/library",
            params={"ids": typed_ids, "include": csv_param(include)},
            user_auth=True,
        )
        return maybe_text(payload, format, title="Library resources")
