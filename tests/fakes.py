from __future__ import annotations

from typing import Any


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

    async def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"kind": "post", "path": path, "body": body})
        return {"data": [{"id": "created"}]}

    async def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"kind": "put", "path": path, "body": body})
        return {}

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append({"kind": "delete", "path": path, "params": params or {}})
        return {}
