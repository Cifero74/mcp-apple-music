"""Personalization, ratings, favorites, replay, and history tools."""

from __future__ import annotations

from typing import Any

from ..api_manifest import RATING_CATALOG_TYPES, RATING_LIBRARY_TYPES
from .common import (
    ClientGetter,
    csv_param,
    maybe_text,
    operation_report,
    paging_params,
    path_segment,
    require_values,
    validate_choice,
)

CATALOG_RATING_CHOICES = tuple(RATING_CATALOG_TYPES)
LIBRARY_RATING_CHOICES = tuple(RATING_LIBRARY_TYPES)
FAVORITE_CHOICES = (
    "albums",
    "artists",
    "songs",
    "music-videos",
    "playlists",
    "stations",
    "library-albums",
    "library-artists",
    "library-songs",
    "library-music-videos",
    "library-playlists",
)


def _rating_segment(domain: str, resource_type: str) -> str:
    if domain == "catalog":
        return validate_choice(resource_type, CATALOG_RATING_CHOICES, "resource_type")
    validate_choice(domain, ("catalog", "library"), "domain")
    if resource_type.startswith("library-"):
        return validate_choice(resource_type, LIBRARY_RATING_CHOICES, "resource_type")
    library_type = f"library-{resource_type}"
    validate_choice(library_type, LIBRARY_RATING_CHOICES, "resource_type")
    return library_type


def _rating_body(value: int) -> dict[str, Any]:
    if value not in {-1, 1}:
        raise ValueError("rating must be -1 or 1; use delete_resource_rating to remove a rating.")
    return {"type": "ratings", "attributes": {"value": value}}


def register_personalization_tools(mcp: Any, get_client: ClientGetter) -> None:
    @mcp.tool()
    async def get_resource_rating(
        domain: str,
        resource_type: str,
        resource_id: str,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get the user's rating for one catalog or library resource."""
        segment = _rating_segment(domain, resource_type)
        path = (
            f"/me/ratings/{path_segment(segment, 'resource_type')}/"
            f"{path_segment(resource_id, 'resource_id')}"
        )
        payload = await get_client().request_structured("GET", path, user_auth=True)
        return maybe_text(payload, format, title=f"Rating {segment}:{resource_id}")

    @mcp.tool()
    async def get_resource_ratings(
        domain: str,
        resource_type: str,
        ids: str,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get the user's ratings for multiple catalog or library resources."""
        segment = _rating_segment(domain, resource_type)
        path = f"/me/ratings/{path_segment(segment, 'resource_type')}"
        payload = await get_client().request_structured(
            "GET",
            path,
            params={"ids": ids},
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Ratings {segment}")

    @mcp.tool()
    async def set_resource_rating(
        domain: str,
        resource_type: str,
        resource_id: str,
        rating: int,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Set a catalog or library resource rating. Rating must be -1 or 1."""
        segment = _rating_segment(domain, resource_type)
        path = (
            f"/me/ratings/{path_segment(segment, 'resource_type')}/"
            f"{path_segment(resource_id, 'resource_id')}"
        )
        body = _rating_body(rating)
        if dry_run:
            return operation_report(
                operation="set_resource_rating",
                path=path,
                method="PUT",
                attempted_ids=[resource_id],
                dry_run=True,
                request_body=body,
            )
        response = await get_client().put(path, body)
        return operation_report(
            operation="set_resource_rating",
            path=path,
            method="PUT",
            attempted_ids=[resource_id],
            request_body=body,
            responses=[response],
        )

    @mcp.tool()
    async def delete_resource_rating(
        domain: str,
        resource_type: str,
        resource_id: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Delete a catalog or library resource rating."""
        segment = _rating_segment(domain, resource_type)
        path = (
            f"/me/ratings/{path_segment(segment, 'resource_type')}/"
            f"{path_segment(resource_id, 'resource_id')}"
        )
        if dry_run:
            return operation_report(
                operation="delete_resource_rating",
                path=path,
                method="DELETE",
                attempted_ids=[resource_id],
                dry_run=True,
            )
        response = await get_client().delete(path)
        return operation_report(
            operation="delete_resource_rating",
            path=path,
            method="DELETE",
            attempted_ids=[resource_id],
            responses=[response],
        )

    @mcp.tool()
    async def add_resources_to_favorites(
        resource_type: str,
        ids: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Add catalog or library resources to the user's favorites."""
        resource = validate_choice(resource_type, FAVORITE_CHOICES, "resource_type")
        path = "/me/favorites"
        attempted = require_values(ids, "ids")
        params = {f"ids[{resource}]": ",".join(attempted)}
        if dry_run:
            return operation_report(
                operation="add_resources_to_favorites",
                path=path,
                attempted_ids=attempted,
                dry_run=True,
                request_params=params,
            )
        response = await get_client().post(path, params=params)
        return operation_report(
            operation="add_resources_to_favorites",
            path=path,
            attempted_ids=attempted,
            request_params=params,
            responses=[response],
        )

    @mcp.tool()
    async def get_replay(
        period: str | None = None,
        year: str | None = None,
        language: str | None = None,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get Apple Music Replay data for the user."""
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            **{"filter[year]": year or period, "l": language},
        )
        payload = await get_client().request_structured(
            "GET",
            "/me/music-summaries",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Replay")

    @mcp.tool()
    async def get_recommendation(
        recommendation_id: str,
        include: str | None = None,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get one Apple Music recommendation by ID."""
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            include=csv_param(include),
        )
        payload = await get_client().request_structured(
            "GET",
            f"/me/recommendations/{path_segment(recommendation_id, 'recommendation_id')}",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Recommendation {recommendation_id}")

    @mcp.tool()
    async def get_recommendation_relationship(
        recommendation_id: str,
        relationship: str,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Fetch a recommendation relationship such as contents."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            (
                f"/me/recommendations/{path_segment(recommendation_id, 'recommendation_id')}/"
                f"{path_segment(relationship, 'relationship')}"
            ),
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Recommendation {relationship}")

    @mcp.tool()
    async def get_recommendations(
        ids: str | None = None,
        include: str | None = None,
        limit: int = 5,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get default or selected Apple Music recommendation groups."""
        params = (
            {"ids": ids, "include": csv_param(include)}
            if ids
            else paging_params(limit=limit, offset=offset, max_limit=10, include=csv_param(include))
        )
        payload = await get_client().request_structured(
            "GET",
            "/me/recommendations",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Recommendations")

    @mcp.tool()
    async def get_heavy_rotation(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get the user's heavy rotation content."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            "/me/history/heavy-rotation",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Heavy rotation")

    @mcp.tool()
    async def get_recently_played(
        limit: int = 10,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get recently played resources such as albums, playlists, and stations."""
        params = paging_params(limit=limit, offset=offset, max_limit=50)
        payload = await get_client().request_structured(
            "GET",
            "/me/recent/played",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Recently played resources")

    @mcp.tool()
    async def get_recently_played_tracks(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get recently played tracks, distinct from recently played resources."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            "/me/recent/played/tracks",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Recently played tracks")

    @mcp.tool()
    async def get_recently_played_stations(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get recently played stations."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            "/me/recent/radio-stations",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Recently played stations")

    @mcp.tool()
    async def get_recently_added_resources(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get resources recently added to the user's library."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            "/me/library/recently-added",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Recently added resources")

    @mcp.tool()
    async def get_user_storefront(format: str = "structured") -> dict[str, Any] | str:
        """Get the user's Apple Music storefront."""
        payload = await get_client().request_structured("GET", "/me/storefront", user_auth=True)
        return maybe_text(payload, format, title="User storefront")

    @mcp.tool()
    async def get_personal_station(
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get the user's personal Apple Music station."""
        params = paging_params(limit=limit, offset=offset, max_limit=100)
        payload = await get_client().request_structured(
            "GET",
            "/me/stations",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title="Personal station")
