"""
Async HTTP client for the Apple Music REST API.

Base URL: https://api.music.apple.com/v1
All methods raise AppleMusicAPIError on non-2xx responses.
"""

from collections.abc import Callable
from typing import Any, Optional

import httpx

from .auth import AppleMusicAuth
from .responses import AppleMusicAPIError, clean_params, error_from_response, structured_response

BASE_URL = "https://api.music.apple.com/v1"
TIMEOUT = 30.0
ClientFactory = Callable[[], httpx.AsyncClient]


def _ids_from_body_or_params(
    body: dict[str, Any] | None,
    params: dict[str, Any] | None,
) -> list[str]:
    if body and isinstance(body.get("data"), list):
        return [
            str(item.get("id"))
            for item in body["data"]
            if isinstance(item, dict) and item.get("id")
        ]
    ids: list[str] = []
    for key, value in clean_params(params).items():
        if key.startswith("ids["):
            ids.extend(str(part).strip() for part in str(value).split(",") if str(part).strip())
    return ids


class AppleMusicClient:
    """Thin async wrapper around the Apple Music REST API."""

    def __init__(self, auth: AppleMusicAuth, client_factory: ClientFactory | None = None):
        self.auth = auth
        self._client_factory = client_factory or (lambda: httpx.AsyncClient())

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
        return await self.request("GET", path, params=params, user_auth=user_auth)

    async def post(
        self,
        path: str,
        body: Optional[dict] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict:
        """POST request (always requires user auth).

        Returns an empty dict for 204 No Content responses.
        """
        return await self.request("POST", path, params=params, body=body, user_auth=True)

    async def post_many(self, path: str, bodies: list[dict]) -> list[dict]:
        """POST several request bodies to one path while reusing one HTTP client."""
        responses: list[dict] = []
        async with self._client_factory() as client:
            for body in bodies:
                response = await self._send_with_client(
                    client,
                    "POST",
                    path,
                    body=body,
                    user_auth=True,
                )
                responses.append(response.json() if response.content else {})
        return responses

    async def post_many_outcomes(
        self,
        path: str,
        bodies: list[dict | None],
        params_list: list[dict[str, Any] | None] | None = None,
    ) -> list[dict[str, Any]]:
        """POST batches and preserve partial success details if a later batch fails."""
        outcomes: list[dict[str, Any]] = []
        async with self._client_factory() as client:
            for index, body in enumerate(bodies):
                params = params_list[index] if params_list else None
                request = {
                    "method": "POST",
                    "path": path,
                    "params": clean_params(params),
                    "body": body,
                }
                attempted_ids = _ids_from_body_or_params(body, params)
                try:
                    response = await self._send_with_client(
                        client,
                        "POST",
                        path,
                        params=params,
                        body=body,
                        user_auth=True,
                    )
                except AppleMusicAPIError as error:
                    outcomes.append(
                        {
                            "batch_index": index,
                            "success": False,
                            "status_code": error.status_code,
                            "request": request,
                            "attempted": {
                                "count": len(attempted_ids),
                                "ids": attempted_ids,
                            },
                            "error": {
                                "message": error.message,
                                "body": error.body,
                            },
                        }
                    )
                    break
                payload = response.json() if response.content else {}
                outcomes.append(
                    {
                        "batch_index": index,
                        "success": True,
                        "status_code": response.status_code,
                        "request": request,
                        "attempted": {
                            "count": len(attempted_ids),
                            "ids": attempted_ids,
                        },
                        "response": payload,
                    }
                )
        return outcomes

    async def put(
        self,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """PUT request, used by ratings endpoints."""
        return await self.request("PUT", path, body=body, user_auth=True)

    async def delete(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict:
        """DELETE request, used by ratings endpoints."""
        return await self.request("DELETE", path, params=params, user_auth=True)

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict] = None,
        user_auth: bool = True,
    ) -> dict:
        """Make a request and return the raw Apple Music response JSON."""
        response = await self._send(method, path, params=params, body=body, user_auth=user_auth)
        return response.json() if response.content else {}

    async def request_structured(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict] = None,
        user_auth: bool = True,
    ) -> dict:
        """Make a request and wrap the response with stable request metadata."""
        payload = await self.request(method, path, params=params, body=body, user_auth=user_auth)
        return structured_response(method=method, path=path, params=params, payload=payload)

    async def _send(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict] = None,
        user_auth: bool = True,
    ) -> httpx.Response:
        async with self._client_factory() as client:
            return await self._send_with_client(
                client,
                method,
                path,
                params=params,
                body=body,
                user_auth=user_auth,
            )

    async def _send_with_client(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        body: Optional[dict] = None,
        user_auth: bool = True,
    ) -> httpx.Response:
        headers = self.auth.get_auth_headers() if user_auth else self.auth.get_catalog_headers()
        if method.upper() in {"POST", "PUT"}:
            headers = {**headers, "Content-Type": "application/json"}

        response = await client.request(
            method.upper(),
            f"{BASE_URL}{path}",
            headers=headers,
            params=clean_params(params),
            json=body if body is not None else None,
            timeout=TIMEOUT,
        )

        if response.is_error:
            raise error_from_response(method, path, response)
        return response

    # ------------------------------------------------------------------ #
    #  Pagination helper                                                   #
    # ------------------------------------------------------------------ #

    async def get_all_pages(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        max_items: int = 500,
        user_auth: bool = True,
    ) -> list[dict]:
        """Fetch all pages of a paginated endpoint, up to max_items."""
        results: list[dict] = []
        offset = 0
        page_size = 100

        while len(results) < max_items:
            page_params = {**(params or {}), "limit": page_size, "offset": offset}
            data = await self.get(path, page_params, user_auth=user_auth)
            items = data.get("data", [])
            results.extend(items)

            next_url = data.get("next")
            if not next_url or not items:
                break
            offset += len(items)

        return results[:max_items]

    async def get_all_pages_structured(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        max_items: int = 500,
        user_auth: bool = True,
    ) -> dict:
        """Fetch all pages and include request/page metadata."""
        results = await self.get_all_pages(
            path,
            params=params,
            max_items=max_items,
            user_auth=user_auth,
        )
        return {
            "request": {
                "method": "GET",
                "path": path,
                "params": clean_params(params),
                "max_items": max_items,
            },
            "data": results,
            "meta": {"count": len(results)},
        }
