"""
Async HTTP client for the Apple Music REST API.

Base URL: https://api.music.apple.com/v1
All methods raise httpx.HTTPStatusError on non-2xx responses.
"""

from typing import Any, Optional

import httpx

from .auth import AppleMusicAuth

API_HOST = "https://api.music.apple.com"
BASE_URL = f"{API_HOST}/v1"
TIMEOUT = 30.0


class AppleMusicClient:
    """Thin async wrapper around the Apple Music REST API."""

    def __init__(self, auth: AppleMusicAuth):
        self.auth = auth

    # ------------------------------------------------------------------ #
    #  Core HTTP helpers                                                   #
    # ------------------------------------------------------------------ #

    async def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        user_auth: bool = True,
    ) -> dict:
        """GET request.

        Args:
            path: API path relative to BASE_URL (e.g. '/me/library/songs').
            params: Optional query parameters.
            user_auth: If True, include the Music-User-Token header.
                       Set False for public catalog endpoints.
        """
        headers = (
            self.auth.get_auth_headers()
            if user_auth
            else self.auth.get_catalog_headers()
        )
        # Strip None values so Apple doesn't get confused
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}{path}",
                headers=headers,
                params=clean_params,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """POST request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        headers = {
            **self.auth.get_auth_headers(),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}{path}",
                headers=headers,
                json=body or {},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def put(
        self,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """PUT request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        headers = {
            **self.auth.get_auth_headers(),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}{path}",
                headers=headers,
                json=body or {},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def delete(self, path: str) -> dict:
        """DELETE request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}{path}",
                headers=self.auth.get_auth_headers(),
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    # ------------------------------------------------------------------ #
    #  Pagination helper                                                 #
    # ------------------------------------------------------------------ #

    async def get_url(self, url: str, user_auth: bool = True) -> dict:
        """GET an Apple Music API URL (e.g. a pagination `next` link).

        Apple returns `next` as a host-relative path such as
        '/v1/me/library/songs?offset=100', so prefix the API host when needed.
        """
        if url.startswith("/"):
            url = f"{API_HOST}{url}"
        headers = (
            self.auth.get_auth_headers()
            if user_auth
            else self.auth.get_catalog_headers()
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()

    async def get_all_pages(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        max_items: int = 500,
        user_auth: bool = True,
        page_size: int = 100,
    ) -> list[dict]:
        """Fetch all pages of a paginated endpoint, up to max_items.

        Prefers the API's `next` URL when present (Apple's recommended approach),
        and falls back to incrementing `offset` otherwise.
        """
        results: list[dict] = []
        offset = 0
        page_size = min(max(1, page_size), 100)
        next_url: Optional[str] = None

        while len(results) < max_items:
            if next_url:
                data = await self.get_url(next_url, user_auth=user_auth)
            else:
                page_params = {
                    **(params or {}),
                    "limit": page_size,
                    "offset": offset,
                }
                data = await self.get(path, page_params, user_auth=user_auth)

            items = data.get("data", [])
            if not items:
                break

            results.extend(items)

            # Check if there are more pages
            next_url = data.get("next")
            if not next_url:
                break
            offset += len(items)

        return results[:max_items]
