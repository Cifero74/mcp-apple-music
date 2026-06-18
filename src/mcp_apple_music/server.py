"""Apple Music MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .auth import AppleMusicAuth
from .client import AppleMusicClient
from .tools import register_tools

mcp = FastMCP(
    "apple-music",
    instructions=(
        "Apple Music integration: search catalog resources, read library resources, "
        "create playlists/folders, add tracks, manage ratings/favorites, and inspect "
        "history, replay, recommendations, and storefront data."
    ),
)

_auth: AppleMusicAuth | None = None
_client: AppleMusicClient | None = None


def _get_client() -> AppleMusicClient:
    """Return the shared AppleMusicClient, initialising lazily."""
    global _auth, _client
    if _client is None:
        _auth = AppleMusicAuth()
        _client = AppleMusicClient(_auth)
    return _client


register_tools(mcp, _get_client)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
