"""Apple Music catalog and library search tools."""

from __future__ import annotations

from typing import Any

from ..api_manifest import CATALOG_RESOURCE_TYPES, LIBRARY_RESOURCE_TYPES
from .common import ClientGetter, csv_param, maybe_text, paging_params, storefront_or_default

DEFAULT_CATALOG_SEARCH_TYPES = "songs,albums,artists,playlists"
DEFAULT_LIBRARY_SEARCH_TYPES = "library-songs,library-albums,library-artists,library-playlists"


def register_search_tools(mcp: Any, get_client: ClientGetter) -> None:
    @mcp.tool()
    async def search_catalog(
        query: str,
        types: str = DEFAULT_CATALOG_SEARCH_TYPES,
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 5,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Search the Apple Music catalog across any documented catalog resource type."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=25,
            term=query,
            types=csv_param(types),
            l=language,
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/search",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title=f"Catalog search: {query}")

    @mcp.tool()
    async def get_catalog_search_hints(
        query: str,
        types: str = ",".join(CATALOG_RESOURCE_TYPES),
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 10,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get Apple Music catalog search hints for a partial term."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            max_limit=25,
            term=query,
            types=csv_param(types),
            l=language,
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/search/hints",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title=f"Catalog search hints: {query}")

    @mcp.tool()
    async def get_catalog_search_suggestions(
        query: str,
        types: str = ",".join(CATALOG_RESOURCE_TYPES),
        storefront: str | None = None,
        language: str | None = None,
        limit: int = 10,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Get Apple Music catalog search suggestions for a query."""
        client = get_client()
        storefront_id = storefront_or_default(client, storefront)
        params = paging_params(
            limit=limit,
            max_limit=25,
            term=query,
            types=csv_param(types),
            l=language,
        )
        payload = await client.request_structured(
            "GET",
            f"/catalog/{storefront_id}/search/suggestions",
            params=params,
            user_auth=False,
        )
        return maybe_text(payload, format, title=f"Catalog search suggestions: {query}")

    @mcp.tool()
    async def search_library(
        query: str,
        types: str = DEFAULT_LIBRARY_SEARCH_TYPES,
        limit: int = 10,
        offset: int = 0,
        format: str = "structured",
    ) -> dict[str, Any] | str:
        """Search within the user's Apple Music library."""
        params = paging_params(
            limit=limit,
            offset=offset,
            max_limit=25,
            term=query,
            types=csv_param(types) or ",".join(LIBRARY_RESOURCE_TYPES),
        )
        payload = await get_client().request_structured(
            "GET",
            "/me/library/search",
            params=params,
            user_auth=True,
        )
        return maybe_text(payload, format, title=f"Library search: {query}")
