"""Catalog, chart, station, and multi-resource Apple Music tools."""

from __future__ import annotations

from typing import Any

from ..api_manifest import CATALOG_RESOURCE_TYPES
from .common import (
    ClientGetter,
    csv_param,
    maybe_text,
    paging_params,
    storefront_or_default,
    validate_choice,
)

CATALOG_CHOICES = tuple(CATALOG_RESOURCE_TYPES)
CATALOG_VIEW_CHOICES = ("albums", "artists", "music-videos", "playlists", "record-labels")
EQUIVALENT_CHOICES = ("albums", "songs", "music-videos")


def register_catalog_tools(mcp: Any, get_client: ClientGetter) -> None:
    @mcp.tool()
    async def get_catalog_resource(
        resource_type: str,
        resource_id: str,
        storefront: str | None = None,
        include: str | None = None,
        language: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get one catalog resource by type and ID."""
        resource = validate_choice(resource_type, CATALOG_CHOICES, "resource_type")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}/{resource_id}"
        params = {"include": csv_param(include), "l": language}
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title=f"Catalog {resource}")

    @mcp.tool()
    async def get_catalog_resources(
        resource_type: str,
        ids: str,
        storefront: str | None = None,
        include: str | None = None,
        language: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get multiple catalog resources of one type by comma-separated IDs."""
        resource = validate_choice(resource_type, CATALOG_CHOICES, "resource_type")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}"
        params = {"ids": ids, "include": csv_param(include), "l": language}
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title=f"Catalog {resource}")

    @mcp.tool()
    async def get_catalog_resources_by_filter(
        resource_type: str,
        filter_name: str,
        filter_values: str,
        storefront: str | None = None,
        include: str | None = None,
        language: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get catalog albums/songs/music videos using documented UPC or ISRC filters."""
        resource = validate_choice(resource_type, ("albums", "songs", "music-videos"), "resource_type")
        valid_filter = "upc" if resource == "albums" else "isrc"
        if filter_name != valid_filter:
            raise ValueError(f"{resource} filter_name must be {valid_filter!r}")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}"
        params = {
            f"filter[{valid_filter}]": filter_values,
            "include": csv_param(include),
            "l": language,
        }
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title=f"Catalog {resource} by {valid_filter.upper()}")

    @mcp.tool()
    async def get_catalog_relationship(
        resource_type: str,
        resource_id: str,
        relationship: str,
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Fetch a relationship for any documented catalog resource."""
        resource = validate_choice(resource_type, CATALOG_CHOICES, "resource_type")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}/{resource_id}/{relationship}"
        params = paging_params(limit=limit, offset=offset, max_limit=100, l=language)
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title=f"Catalog {resource} {relationship}")

    @mcp.tool()
    async def get_catalog_view(
        resource_type: str,
        resource_id: str,
        view: str,
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Fetch a relationship view for resources that support catalog views."""
        resource = validate_choice(resource_type, CATALOG_VIEW_CHOICES, "resource_type")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}/{resource_id}/view/{view}"
        params = paging_params(limit=limit, offset=offset, max_limit=100, l=language)
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title=f"Catalog {resource} view {view}")

    @mcp.tool()
    async def get_equivalent_catalog_ids(
        resource_type: str,
        resource_id: str,
        storefront: str | None = None,
        language: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get equivalent catalog IDs for albums, songs, or music videos."""
        resource = validate_choice(resource_type, EQUIVALENT_CHOICES, "resource_type")
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/{resource}/{resource_id}/equivalents"
        payload = await client.request_structured(
            "GET",
            path,
            params={"l": language},
            user_auth=False,
        )
        return maybe_text(payload, format, title=f"Equivalent {resource}")

    @mcp.tool()
    async def get_catalog_charts(
        storefront: str | None = None,
        types: str = "songs,albums,playlists,music-videos",
        chart: str | None = None,
        genre: str | None = None,
        language: str | None = None,
        limit: int = 20,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get Apple Music catalog charts."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=50,
            types=csv_param(types),
            chart=chart,
            genre=genre,
            l=language,
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/charts",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title="Catalog charts")

    @mcp.tool()
    async def get_catalog_playlist_charts(
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 20,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get catalog playlist charts for a storefront."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(limit=limit, offset=offset, max_limit=50, l=language)
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/playlists/charts",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title="Catalog playlist charts")

    @mcp.tool()
    async def get_live_radio_stations(
        storefront: str | None = None,
        featured: str | None = None,
        language: str | None = None,
        limit: int = 25,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get catalog stations, including Apple Music live radio when featured is supplied."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            **{"filter[featured]": featured, "l": language},
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/stations",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title="Catalog stations")

    @mcp.tool()
    async def get_station_genres(
        storefront: str | None = None,
        genre_ids: str | None = None,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get all or selected station genres."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        path = f"/catalog/{storefront_id}/station-genres"
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            ids=csv_param(genre_ids),
            l=language,
        )
        payload = await client.request_structured("GET", path, params=params, user_auth=False)
        return maybe_text(payload, format, title="Station genres")

    @mcp.tool()
    async def get_catalog_genres(
        storefront: str | None = None,
        genre_ids: str | None = None,
        language: str | None = None,
        limit: int = 100,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get all or selected catalog genres for a storefront."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=100,
            ids=csv_param(genre_ids),
            l=language,
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/genres",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title="Catalog genres")

    @mcp.tool()
    async def get_multiple_catalog_resources(
        typed_ids: str,
        storefront: str | None = None,
        include: str | None = None,
        language: str | None = None,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get multiple catalog resources by typed IDs such as songs:123,albums:456."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = {"ids": typed_ids, "include": csv_param(include), "l": language}
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title="Catalog resources")

    @mcp.tool()
    async def test_apple_music_api_connectivity(format: str = "structured") -> dict[str, Any] | str:
        """Call Apple's lightweight connectivity test endpoint."""
        client = get_client()
        payload = await client.request_structured("GET", "/test", user_auth=False)
        return maybe_text(payload, format, title="Apple Music API connectivity")
