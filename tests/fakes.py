from __future__ import annotations

import asyncio
from typing import Any

from mcp_apple_music.tools import register_tools


class FakeMCP:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


class FakeAuth:
    def get_storefront(self) -> str:
        return "us"


class FakeClient:
    def __init__(self) -> None:
        self.auth = FakeAuth()
        self.calls: list[dict[str, Any]] = []

    async def request_structured(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        user_auth: bool = True,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "kind": "request_structured",
                "method": method,
                "path": path,
                "params": params or {},
                "body": body,
                "user_auth": user_auth,
            }
        )
        return {
            "request": {
                "method": method,
                "path": path,
                "params": params or {},
            },
            "data": [{"id": "1", "type": "songs", "attributes": {"name": "Track"}}],
            "raw": {"data": [{"id": "1"}]},
        }

    async def post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append({"kind": "post", "path": path, "body": body, "params": params or {}})
        return {"data": [{"id": "created"}]}

    async def post_many(self, path: str, bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        responses = []
        for body in bodies:
            self.calls.append({"kind": "post", "path": path, "body": body, "params": {}})
            responses.append({"data": [{"id": "created"}]})
        return responses

    async def post_many_outcomes(
        self,
        path: str,
        bodies: list[dict[str, Any] | None],
        params_list: list[dict[str, Any] | None] | None = None,
    ) -> list[dict[str, Any]]:
        outcomes = []
        for index, body in enumerate(bodies):
            params = params_list[index] if params_list else {}
            self.calls.append({"kind": "post", "path": path, "body": body, "params": params or {}})
            attempted_ids = []
            if body and isinstance(body.get("data"), list):
                attempted_ids = [item["id"] for item in body["data"]]
            for key, value in (params or {}).items():
                if key.startswith("ids["):
                    attempted_ids.extend(part.strip() for part in value.split(",") if part.strip())
            outcomes.append(
                {
                    "batch_index": index,
                    "success": True,
                    "status_code": 200,
                    "request": {"method": "POST", "path": path, "params": params or {}, "body": body},
                    "attempted": {"count": len(attempted_ids), "ids": attempted_ids},
                    "response": {"data": [{"id": "created"}]},
                }
            )
        return outcomes

    async def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"kind": "put", "path": path, "body": body})
        return {}

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"kind": "delete", "path": path, "params": params or {}})
        return {}


def build_tools():
    fake_mcp = FakeMCP()
    client = FakeClient()
    register_tools(fake_mcp, lambda: client)
    return fake_mcp.tools, client


def run(coro):
    return asyncio.run(coro)
