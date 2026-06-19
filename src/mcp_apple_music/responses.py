"""Structured response and error helpers for Apple Music API calls."""

from __future__ import annotations

from typing import Any

import httpx


class AppleMusicAPIError(httpx.HTTPStatusError):
    """HTTP error with stable Apple Music request metadata."""

    def __init__(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        message: str,
        body: Any | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.method = method.upper()
        self.path = path
        self.status_code = status_code
        self.message = message
        self.body = body
        request = getattr(response, "request", None) or httpx.Request(
            self.method,
            f"https://api.music.apple.com/v1{path}",
        )
        self.response = response or httpx.Response(status_code, request=request)
        super().__init__(self._formatted_message(), request=request, response=self.response)

    def _formatted_message(self) -> str:
        return f"{self.method} {self.path} failed with HTTP {self.status_code}: {self.message}"

    def __str__(self) -> str:
        return self._formatted_message()


def clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Remove params Apple should not receive while preserving falsey values."""
    return {key: value for key, value in (params or {}).items() if value is not None}


def structured_response(
    *,
    method: str,
    path: str,
    payload: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap an Apple response with stable request metadata."""
    return {
        "request": {
            "method": method.upper(),
            "path": path,
            "params": clean_params(params),
        },
        "data": payload.get("data", []),
        "results": payload.get("results", {}),
        "meta": payload.get("meta", {}),
        "next": payload.get("next"),
        "raw": payload,
    }


def error_from_response(method: str, path: str, response: Any) -> AppleMusicAPIError:
    try:
        body = response.json()
    except Exception:
        body = getattr(response, "text", "") or None

    message = extract_error_message(body) or getattr(response, "reason_phrase", "Apple Music API error")
    return AppleMusicAPIError(
        method=method.upper(),
        path=path,
        status_code=response.status_code,
        message=message,
        body=body,
        response=response,
    )


def extract_error_message(body: Any | None) -> str:
    if isinstance(body, dict):
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                return str(first.get("detail") or first.get("title") or first.get("code") or "")
        return str(body.get("message") or "")
    if isinstance(body, str):
        return body[:500]
    return ""
