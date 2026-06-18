"""Shared helpers for Apple Music MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..client import AppleMusicClient
from ..responses import clean_params

ClientGetter = Callable[[], AppleMusicClient]
ResponseFormat = str


def split_values(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize comma-separated MCP args and native lists into clean strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def csv_param(value: str | list[str] | tuple[str, ...] | None) -> str | None:
    values = split_values(value)
    return ",".join(values) if values else None


def clamp(value: int, minimum: int, maximum: int) -> int:
    return min(max(minimum, int(value)), maximum)


def positive_offset(offset: int) -> int:
    return max(0, int(offset))


def storefront_or_default(client: AppleMusicClient, storefront: str | None = None) -> str:
    return (storefront or client.auth.get_storefront()).strip().lower()


def paging_params(
    *,
    limit: int | None = None,
    offset: int | None = None,
    max_limit: int = 100,
    **extra: Any,
) -> dict[str, Any]:
    params = dict(extra)
    if limit is not None:
        params["limit"] = clamp(limit, 1, max_limit)
    if offset is not None:
        params["offset"] = positive_offset(offset)
    return clean_params(params)


def relationship_body(ids: str | list[str], resource_type: str) -> dict[str, Any]:
    return {"data": [{"id": item_id, "type": resource_type} for item_id in split_values(ids)]}


def attributes_body(**attributes: Any) -> dict[str, Any]:
    return {"attributes": clean_params(attributes)}


def with_relationship(
    body: dict[str, Any],
    relationship: str,
    resource_type: str,
    ids: str | list[str] | None,
) -> dict[str, Any]:
    values = split_values(ids)
    if values:
        body.setdefault("relationships", {})[relationship] = {
            "data": [{"id": item_id, "type": resource_type} for item_id in values]
        }
    return body


def operation_report(
    *,
    operation: str,
    path: str,
    attempted_ids: list[str] | None = None,
    dry_run: bool = False,
    request_body: dict[str, Any] | None = None,
    responses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attempted = attempted_ids or []
    return {
        "operation": operation,
        "dry_run": dry_run,
        "request": {
            "method": "POST",
            "path": path,
            "body": request_body or {},
        },
        "attempted": {
            "count": len(attempted),
            "ids": attempted,
        },
        "responses": responses or [],
    }


def as_text_resource_list(payload: dict[str, Any], title: str) -> str:
    rows = payload.get("data") or payload.get("raw", {}).get("data") or []
    if not rows:
        return f"{title}: no results."
    lines = [f"{title}: {len(rows)} result(s)"]
    for index, item in enumerate(rows, 1):
        attributes = item.get("attributes", {})
        name = attributes.get("name") or attributes.get("title") or item.get("id", "?")
        artist = attributes.get("artistName")
        suffix = f" - {artist}" if artist else ""
        lines.append(f"{index}. {name}{suffix} | {item.get('type', '?')}:{item.get('id', '?')}")
    return "\n".join(lines)


def maybe_text(
    payload: dict[str, Any],
    response_format: ResponseFormat = "structured",
    *,
    title: str = "Apple Music response",
) -> dict[str, Any] | str:
    if response_format.lower() in {"text", "summary", "human"}:
        return as_text_resource_list(payload, title)
    return payload


def require_values(value: str | list[str], label: str) -> list[str]:
    values = split_values(value)
    if not values:
        raise ValueError(f"{label} must include at least one value.")
    return values


def validate_choice(value: str, choices: tuple[str, ...], label: str) -> str:
    normalized = value.strip()
    if normalized not in choices:
        joined = ", ".join(choices)
        raise ValueError(f"{label} must be one of: {joined}")
    return normalized
