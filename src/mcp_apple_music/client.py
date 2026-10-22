"""
Async HTTP client for the Apple Music REST API.

Base URL: https://api.music.apple.com/v1
All methods raise AppleMusicAPIError (a subclass of httpx.HTTPStatusError)
on non-2xx responses, with a human-readable explanation of what went wrong.
"""

from typing import Any, Optional

import httpx

from .auth import AppleMusicAuth

API_HOST = "https://api.music.apple.com"
BASE_URL = f"{API_HOST}/v1"
TIMEOUT = 30.0


class AppleMusicAPIError(httpx.HTTPStatusError):
    """Non-2xx response from Apple Music, with a hint the model can act on."""


def _storefront_from_path(path: str) -> str | None:
    """Extract the storefront from a '/v1/catalog/{storefront}/...' path."""
    parts = path.split("/")
    if "catalog" in parts:
        idx = parts.index("catalog")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def _raise_for_status(response: httpx.Response) -> None:
    """Raise AppleMusicAPIError with a readable message on non-2xx responses."""
    if response.is_success:
        return

    status = response.status_code
    path = response.request.url.path
    storefront = _storefront_from_path(path)

    detail = ""
    try:
        errors = response.json().get("errors", [])
        if errors:
            detail = errors[0].get("detail") or errors[0].get("title") or ""
    except ValueError:
        pass

    if status == 401:
        hint = (
            "the developer token was rejected. Check the Team ID, the Key ID "
            "and the MusicKit .p8 key."
        )
    elif status == 403 and "/me/" in path:
        hint = (
            "the Music User Token is invalid or expired. Run "
            "`mcp-apple-music-setup` again and log in to Apple Music."
        )
    elif status == 404 and storefront:
        hint = (
            f"not found in the '{storefront}' storefront. Check the ID, and that "
            "the storefront is a two-letter country code such as 'it' or 'us'."
        )
    elif status == 404:
        hint = (
            "not found. Library IDs start with 'i.', 'l.' or 'p.'; catalog "
            "playlist IDs start with 'pl.'; catalog songs and albums are numeric."
        )
    elif status == 429:
        hint = "rate limited by Apple Music. Wait a moment and retry."
    elif status >= 500:
        hint = "Apple Music is having problems. Retry later."
    else:
        hint = "the request was rejected."

    message = f"Apple Music API error {status}: {hint}"
    if detail:
        message += f" (Apple says: {detail})"
    raise AppleMusicAPIError(message, request=response.request, response=response)


class AppleMusicClient:
    """Thin async wrapper around the Apple Music REST API."""

    def __init__(self, auth: AppleMusicAuth):
        self.auth = auth

    # ------------------------------------------------------------------ #
    #  Core HTTP helpers                                                   #
    # ------------------------------------------------------------------ #

    async def _send(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        body: dict | None = None,
    ) -> dict:
        """Send a request and return the decoded JSON ({} for empty bodies)."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=body,
                timeout=TIMEOUT,
            )
        _raise_for_status(response)
        return response.json() if response.content else {}

    def _write_headers(self) -> dict[str, str]:
        return {**self.auth.get_auth_headers(), "Content-Type": "application/json"}

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
        return await self._send("GET", f"{BASE_URL}{path}", headers, params=clean_params)

    async def post(
        self,
        path: str,
        body: Optional[dict] = None,
        params: dict[str, Any] | None = None,
    ) -> dict:
        """POST request (always requires user auth).

        Without a body (e.g. POST /me/library?ids[...]=...), no payload is sent.
        Returns an empty dict for 202/204 responses without a body.
        """
        return await self._send(
            "POST", f"{BASE_URL}{path}", self._write_headers(),
            params=params, body=body,
        )

    async def put(
        self,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """PUT request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        return await self._send(
            "PUT", f"{BASE_URL}{path}", self._write_headers(), body=body or {},
        )

    async def delete(self, path: str) -> dict:
        """DELETE request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        return await self._send(
            "DELETE", f"{BASE_URL}{path}", self.auth.get_auth_headers(),
        )

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
        return await self._send("GET", url, headers)

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
