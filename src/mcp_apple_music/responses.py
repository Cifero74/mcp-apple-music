"""Structured response and error helpers for Apple Music API calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppleMusicAPIError(Exception):
    method: str
    path: str
    status_code: int
    message: str
    body: Any | None = None

    def __str__(self) -> str:
        return f"{self.method} {self.path} failed with HTTP {self.status_code}: {self.message}"


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
