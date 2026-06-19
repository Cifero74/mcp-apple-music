"""Playlist and playlist-folder write tools."""

from __future__ import annotations

from typing import Any

from .common import (
    ClientGetter,
    attributes_body,
    clamp,
    operation_report,
    relationship_body,
    require_values,
    validate_choice,
    with_relationship,
)

PLAYLIST_TRACK_TYPES = ("songs", "library-songs")
DUPLICATE_HANDLING_NOTE = (
    "Apple Music API behavior controls duplicates unless the caller prefetches playlist tracks."
)


def register_playlist_tools(mcp: Any, get_client: ClientGetter) -> None:
    @mcp.tool()
    async def create_playlist(
        name: str,
        description: str = "",
        track_ids: str | list[str] | None = None,
        track_type: str = "songs",
        parent_folder_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a library playlist, optionally seeded with tracks and a parent folder."""
        validate_choice(track_type, PLAYLIST_TRACK_TYPES, "track_type")
        path = "/me/library/playlists"
        body = attributes_body(name=name, description=description or None)
        with_relationship(body, "tracks", track_type, track_ids)
        with_relationship(body, "parent", "library-playlist-folders", parent_folder_id)
        attempted = require_values(track_ids, "track_ids") if track_ids else []

        if dry_run:
            return operation_report(
                operation="create_playlist",
                path=path,
                attempted_ids=attempted,
                dry_run=True,
                request_body=body,
            )

        response = await get_client().post(path, body)
        return operation_report(
            operation="create_playlist",
            path=path,
            attempted_ids=attempted,
            request_body=body,
            responses=[response],
        )

    @mcp.tool()
    async def add_tracks_to_playlist(
        playlist_id: str,
        track_ids: str | list[str],
        track_type: str = "library-songs",
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Add catalog songs or library songs to a library playlist with safe batching."""
        track_kind = validate_choice(track_type, PLAYLIST_TRACK_TYPES, "track_type")
        ids = require_values(track_ids, "track_ids")
        size = clamp(batch_size, 1, 100)
        path = f"/me/library/playlists/{playlist_id}/tracks"
        batches = [ids[index : index + size] for index in range(0, len(ids), size)]
        request_bodies = [relationship_body(batch, track_kind) for batch in batches]
        responses = [] if dry_run else await get_client().post_many(path, request_bodies)
        request_body = {"batches": request_bodies} if dry_run else None

        return {
            **operation_report(
                operation="add_tracks_to_playlist",
                path=path,
                attempted_ids=ids,
                dry_run=dry_run,
                request_body=request_body,
                responses=responses,
            ),
            "batch_size": size,
            "batch_count": len(batches),
            "duplicate_handling": DUPLICATE_HANDLING_NOTE,
        }

    @mcp.tool()
    async def create_playlist_folder(
        name: str,
        parent_folder_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a library playlist folder."""
        path = "/me/library/playlist-folders"
        body = attributes_body(name=name)
        with_relationship(body, "parent", "library-playlist-folders", parent_folder_id)
        if dry_run:
            return operation_report(
                operation="create_playlist_folder",
                path=path,
                dry_run=True,
                request_body=body,
            )
        response = await get_client().post(path, body)
        return operation_report(
            operation="create_playlist_folder",
            path=path,
            request_body=body,
            responses=[response],
        )
