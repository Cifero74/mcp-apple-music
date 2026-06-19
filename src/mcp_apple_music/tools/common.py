"""Shared helpers for Apple Music MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import quote

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


def path_segment(value: str, label: str) -> str:
    """Encode one dynamic URL path segment without allowing dot segments."""
    segment = str(value).strip()
    if not segment:
        raise ValueError(f"{label} must include a value.")
    if segment in {".", ".."}:
        raise ValueError(f"{label} cannot be a dot segment.")
    return quote(segment, safe="")


def typed_ids_params(
    typed_ids: str | list[str],
    *,
    choices: tuple[str, ...],
    label: str = "typed_ids",
) -> dict[str, str]:
    params: dict[str, list[str]] = {}
    for item in require_values(typed_ids, label):
        resource_type, separator, item_id = item.partition(":")
        resource_type = resource_type.strip()
        item_id = item_id.strip()
        if not separator or not resource_type or not item_id:
            raise ValueError(f"{label} entries must use resource_type:id.")
        validate_choice(resource_type, choices, "resource_type")
        params.setdefault(f"ids[{resource_type}]", []).append(item_id)
    return {key: ",".join(values) for key, values in params.items()}


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


def _relationship_data(ids: str | list[str] | None, resource_type: str) -> list[dict[str, str]]:
    return [{"id": item_id, "type": resource_type} for item_id in split_values(ids)]


def relationship_body(ids: str | list[str], resource_type: str) -> dict[str, Any]:
    return {"data": _relationship_data(ids, resource_type)}


def attributes_body(**attributes: Any) -> dict[str, Any]:
    return {"attributes": clean_params(attributes)}


def with_relationship(
    body: dict[str, Any],
    relationship: str,
    resource_type: str,
    ids: str | list[str] | None,
) -> dict[str, Any]:
    data = _relationship_data(ids, resource_type)
    if data:
        body.setdefault("relationships", {})[relationship] = {
            "data": data
        }
    return body


def operation_report(
    *,
    operation: str,
    path: str,
    method: str = "POST",
    attempted_ids: list[str] | None = None,
    dry_run: bool = False,
    request_params: dict[str, Any] | None = None,
    request_body: dict[str, Any] | None = None,
    responses: list[dict[str, Any]] | None = None,
    batch_outcomes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    attempted = attempted_ids or []
    request: dict[str, Any] = {"method": method.upper(), "path": path}
    if request_params is not None:
        request["params"] = clean_params(request_params)
    if request_body is not None:
        request["body"] = request_body
    batches = batch_outcomes or []
    failed_batches = [batch for batch in batches if batch.get("success") is False]
    succeeded_ids = [
        item_id
        for batch in batches
        if batch.get("success") is True
        for item_id in batch.get("attempted", {}).get("ids", [])
    ]
    failed_ids = [
        item_id
        for batch in failed_batches
        for item_id in batch.get("attempted", {}).get("ids", [])
    ]
    pending_ids = attempted[len(succeeded_ids) + len(failed_ids) :] if failed_batches else []
    status = "dry_run" if dry_run else "partial_failure" if failed_batches else "ok"
    return {
        "operation": operation,
        "success": not failed_batches,
        "status": status,
        "dry_run": dry_run,
        "request": request,
        "attempted": {
            "count": len(attempted),
            "ids": attempted,
        },
        "succeeded": {
            "count": len(succeeded_ids) if batches else (0 if dry_run else len(attempted)),
            "ids": succeeded_ids if batches else ([] if dry_run else attempted),
        },
        "failed": {
            "count": len(failed_ids),
            "ids": failed_ids,
        },
        "pending": {
            "count": len(pending_ids),
            "ids": pending_ids,
        },
        "responses": responses or [],
        "batches": batches,
        "next_action": (
            "No request was sent; review the request and rerun with dry_run=False."
            if dry_run
            else "Do not retry the full operation; retry only failed and pending IDs."
            if failed_batches
            else "Operation accepted by Apple Music."
        ),
    }


def as_text_resource_list(payload: dict[str, Any], title: str) -> str:
    rows = payload.get("data") or payload.get("raw", {}).get("data") or []
    if not rows:
        results = payload.get("results") or payload.get("raw", {}).get("results") or {}
        for group in results.values():
            if isinstance(group, dict):
                rows.extend(group.get("data") or [])
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
