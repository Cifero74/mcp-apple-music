"""Tool registration for the Apple Music MCP server."""

from __future__ import annotations

from typing import Any

from ..api_manifest import endpoint_tool_map
from .catalog import register_catalog_tools
from .common import ClientGetter
from .library import register_library_tools
from .personalization import register_personalization_tools
from .playlists import register_playlist_tools
from .search import register_search_tools

EXTRA_TOOL_NAMES = frozenset({"get_library_playlist_folder"})
TOOL_NAMES = frozenset(endpoint_tool_map().values()) | EXTRA_TOOL_NAMES


def register_tools(mcp: Any, get_client: ClientGetter) -> None:
    register_search_tools(mcp, get_client)
    register_catalog_tools(mcp, get_client)
    register_library_tools(mcp, get_client)
    register_playlist_tools(mcp, get_client)
    register_personalization_tools(mcp, get_client)
