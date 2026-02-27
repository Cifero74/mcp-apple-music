"""
Apple Music MCP Server
======================
Exposes Apple Music library, catalog, and playlist management as MCP tools
that Claude can call directly.

Tools provided:
  - search_catalog          Search Apple Music catalog
  - search_library          Search your personal library
  - get_library_songs       List songs in your library
  - get_library_albums      List albums in your library
  - get_library_artists     List artists in your library
  - get_library_playlists   List all your playlists
  - get_playlist_tracks     Get tracks inside a playlist
  - create_playlist         Create a new playlist
  - add_tracks_to_playlist  Add songs to a playlist
  - get_recently_played     See what you listened to recently
  - get_recommendations     Get personalised Apple Music picks
"""

from mcp.server.fastmcp import FastMCP

from .auth import AppleMusicAuth
from .client import AppleMusicClient

# ------------------------------------------------------------------ #
#  Initialise server, auth, and client (lazy — credentials loaded on  #
#  first actual request, not at import time).                         #
# ------------------------------------------------------------------ #

mcp = FastMCP(
    "apple-music",
    instructions="Apple Music integration: search catalog, manage library and playlists.",
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


# ------------------------------------------------------------------ #
#  Formatting helpers                                                  #
# ------------------------------------------------------------------ #


def _fmt_song(item: dict, index: int) -> str:
    a = item.get("attributes", {})
    return (
        f"  {index}. {a.get('name', '?')} — {a.get('artistName', '?')}"
        f" | Album: {a.get('albumName', '?')} | ID: {item.get('id', '?')}"
    )


def _fmt_album(item: dict, index: int) -> str:
    a = item.get("attributes", {})
    year = (a.get("releaseDate") or "")[:4]
    return (
        f"  {index}. {a.get('name', '?')} — {a.get('artistName', '?')}"
        f" ({year}) | ID: {item.get('id', '?')}"
    )


def _fmt_artist(item: dict, index: int) -> str:
    a = item.get("attributes", {})
    return f"  {index}. {a.get('name', '?')} | ID: {item.get('id', '?')}"


def _fmt_playlist(item: dict, index: int) -> str:
    a = item.get("attributes", {})
    desc = a.get("description") or {}
    desc_text = (desc.get("standard", "") if isinstance(desc, dict) else "")[:60]
    line = (
        f"  {index}. [{item.get('id', '?')}] {a.get('name', '?')}"
        f" ({a.get('trackCount', '?')} tracks)"
    )
    if desc_text:
        line += f" — {desc_text}"
    return line


# ------------------------------------------------------------------ #
#  Tool: search_catalog                                               #
# ------------------------------------------------------------------ #


@mcp.tool()
async def search_catalog(
    query: str,
    types: str = "songs,albums,artists",
    limit: int = 5,
) -> str:
    """Search the Apple Music catalog for songs, albums, artists, or playlists.

    Args:
        query: Search term (e.g. "Radiohead", "Bohemian Rhapsody").
        types: Comma-separated resource types to include.
               Options: songs, albums, artists, playlists  (default: songs,albums,artists)
        limit: Results per type, 1–25 (default 5).
    """
    client = _get_client()
    storefront = client.auth.get_storefront()
    data = await client.get(
        f"/catalog/{storefront}/search",
        params={"term": query, "types": types, "limit": min(max(1, limit), 25)},
        user_auth=False,
    )
    results = data.get("results", {})
    lines = [f"🔍 Catalog search: '{query}'\n"]

    if songs := results.get("songs", {}).get("data", []):
        lines.append("🎵 Songs:")
        for i, s in enumerate(songs, 1):
            lines.append(_fmt_song(s, i))

    if albums := results.get("albums", {}).get("data", []):
        lines.append("\n💿 Albums:")
        for i, a in enumerate(albums, 1):
            lines.append(_fmt_album(a, i))

    if artists := results.get("artists", {}).get("data", []):
        lines.append("\n👤 Artists:")
        for i, a in enumerate(artists, 1):
            lines.append(_fmt_artist(a, i))

    if playlists := results.get("playlists", {}).get("data", []):
        lines.append("\n📋 Playlists:")
        for i, p in enumerate(playlists, 1):
            a = p.get("attributes", {})
            lines.append(
                f"  {i}. {a.get('name', '?')} — {a.get('curatorName', '')} | ID: {p.get('id', '?')}"
            )

    if len(lines) == 1:
        return f"No results found for '{query}'."
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: search_library                                               #
# ------------------------------------------------------------------ #


@mcp.tool()
async def search_library(
    query: str,
    types: str = "library-songs,library-albums,library-artists,library-playlists",
    limit: int = 10,
) -> str:
    """Search within your personal Apple Music library.

    Args:
        query: Search term.
        types: Comma-separated types.
               Options: library-songs, library-albums, library-artists, library-playlists
        limit: Results per type, 1–25 (default 10).
    """
    client = _get_client()
    data = await client.get(
        "/me/library/search",
        params={"term": query, "types": types, "limit": min(max(1, limit), 25)},
    )
    results = data.get("results", {})
    lines = [f"🔍 Library search: '{query}'\n"]

    if songs := results.get("library-songs", {}).get("data", []):
        lines.append("🎵 Songs:")
        for i, s in enumerate(songs, 1):
            lines.append(_fmt_song(s, i))

    if albums := results.get("library-albums", {}).get("data", []):
        lines.append("\n💿 Albums:")
        for i, a in enumerate(albums, 1):
            lines.append(_fmt_album(a, i))

    if artists := results.get("library-artists", {}).get("data", []):
        lines.append("\n👤 Artists:")
        for i, a in enumerate(artists, 1):
            lines.append(_fmt_artist(a, i))

    if playlists := results.get("library-playlists", {}).get("data", []):
        lines.append("\n📋 Playlists:")
        for i, p in enumerate(playlists, 1):
            lines.append(_fmt_playlist(p, i))

    if len(lines) == 1:
        return f"Nothing found in your library for '{query}'."
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_library_songs                                            #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_library_songs(limit: int = 25, offset: int = 0) -> str:
    """List songs saved in your Apple Music library.

    Args:
        limit: Number of songs to return, 1–100 (default 25).
        offset: Pagination offset for retrieving subsequent pages (default 0).
    """
    client = _get_client()
    data = await client.get(
        "/me/library/songs",
        params={"limit": min(max(1, limit), 100), "offset": max(0, offset)},
    )
    songs = data.get("data", [])
    total = data.get("meta", {}).get("total", "?")

    if not songs:
        return "No songs found in your library."

    lines = [f"🎵 Library Songs — showing {offset + 1}–{offset + len(songs)} of {total}:\n"]
    for i, s in enumerate(songs, offset + 1):
        lines.append(_fmt_song(s, i))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_library_albums                                           #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_library_albums(limit: int = 25, offset: int = 0) -> str:
    """List albums saved in your Apple Music library.

    Args:
        limit: Number of albums to return, 1–100 (default 25).
        offset: Pagination offset (default 0).
    """
    client = _get_client()
    data = await client.get(
        "/me/library/albums",
        params={"limit": min(max(1, limit), 100), "offset": max(0, offset)},
    )
    albums = data.get("data", [])
    total = data.get("meta", {}).get("total", "?")

    if not albums:
        return "No albums found in your library."

    lines = [f"💿 Library Albums — showing {offset + 1}–{offset + len(albums)} of {total}:\n"]
    for i, a in enumerate(albums, offset + 1):
        lines.append(_fmt_album(a, i))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_library_artists                                          #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_library_artists(limit: int = 25, offset: int = 0) -> str:
    """List artists in your Apple Music library.

    Args:
        limit: Number of artists to return, 1–100 (default 25).
        offset: Pagination offset (default 0).
    """
    client = _get_client()
    data = await client.get(
        "/me/library/artists",
        params={"limit": min(max(1, limit), 100), "offset": max(0, offset)},
    )
    artists = data.get("data", [])

    if not artists:
        return "No artists found in your library."

    lines = ["👤 Library Artists:\n"]
    for i, a in enumerate(artists, offset + 1):
        lines.append(_fmt_artist(a, i))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_library_playlists                                        #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_library_playlists(limit: int = 100) -> str:
    """List all playlists in your Apple Music library.

    Args:
        limit: Maximum number of playlists to return, 1–100 (default 100).
    """
    client = _get_client()
    data = await client.get(
        "/me/library/playlists",
        params={"limit": min(max(1, limit), 100)},
    )
    playlists = data.get("data", [])

    if not playlists:
        return "No playlists found in your library."

    lines = [f"📋 Your Playlists ({len(playlists)} found):\n"]
    for i, p in enumerate(playlists, 1):
        lines.append(_fmt_playlist(p, i))
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_playlist_tracks                                          #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_playlist_tracks(playlist_id: str, limit: int = 100) -> str:
    """Get the tracks inside a specific playlist.

    Args:
        playlist_id: Library playlist ID (starts with 'p.').
                     Use get_library_playlists to find IDs.
        limit: Maximum tracks to return, 1–100 (default 100).
    """
    client = _get_client()
    data = await client.get(
        f"/me/library/playlists/{playlist_id}/tracks",
        params={"limit": min(max(1, limit), 100)},
    )
    tracks = data.get("data", [])

    if not tracks:
        return f"No tracks found in playlist '{playlist_id}'."

    lines = [f"🎵 Tracks in playlist [{playlist_id}] — {len(tracks)} tracks:\n"]
    for i, t in enumerate(tracks, 1):
        a = t.get("attributes", {})
        lines.append(
            f"  {i}. {a.get('name', '?')} — {a.get('artistName', '?')}"
            f" | Type: {t.get('type', '?')} | ID: {t.get('id', '?')}"
        )
    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: create_playlist                                              #
# ------------------------------------------------------------------ #


@mcp.tool()
async def create_playlist(name: str, description: str = "") -> str:
    """Create a new playlist in your Apple Music library.

    Args:
        name: Name for the new playlist.
        description: Optional short description.
    """
    client = _get_client()
    body: dict = {"attributes": {"name": name}}
    if description:
        body["attributes"]["description"] = description

    data = await client.post("/me/library/playlists", body)

    if data.get("data"):
        pl = data["data"][0]
        pl_id = pl.get("id", "?")
        pl_name = pl.get("attributes", {}).get("name", name)
        return f"✅ Playlist created!\nName: {pl_name}\nID: {pl_id}"

    return f"✅ Playlist '{name}' created successfully."


# ------------------------------------------------------------------ #
#  Tool: add_tracks_to_playlist                                       #
# ------------------------------------------------------------------ #


@mcp.tool()
async def add_tracks_to_playlist(
    playlist_id: str,
    track_ids: list[str],
    track_type: str = "library-songs",
) -> str:
    """Add tracks to an existing playlist.

    Args:
        playlist_id: The target playlist ID (starts with 'p.').
        track_ids: List of track IDs to add.
        track_type: 'library-songs' for tracks from your library (default),
                    'songs' for catalog tracks found via search_catalog.
    """
    if not track_ids:
        return "❌ No track IDs provided."

    client = _get_client()
    body = {"data": [{"id": tid, "type": track_type} for tid in track_ids]}
    await client.post(f"/me/library/playlists/{playlist_id}/tracks", body)

    return (
        f"✅ Added {len(track_ids)} track(s) to playlist [{playlist_id}].\n"
        f"   Track IDs: {', '.join(track_ids)}"
    )


# ------------------------------------------------------------------ #
#  Tool: get_recently_played                                          #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_recently_played(limit: int = 10) -> str:
    """Get your recently played albums, playlists, and stations.

    Note: Apple Music API returns recently-played containers (albums,
    playlists, stations) rather than individual tracks.

    Args:
        limit: Number of items to return, 1–50 (default 10).
    """
    client = _get_client()
    data = await client.get(
        "/me/recent/played",
        params={"limit": min(max(1, limit), 50)},
    )
    items = data.get("data", [])

    if not items:
        return "No recently played items found."

    lines = [f"🕐 Recently Played ({len(items)} items):\n"]
    for i, item in enumerate(items, 1):
        a = item.get("attributes", {})
        t = item.get("type", "")
        pid = item.get("id", "?")
        name = a.get("name", "?")

        if "album" in t:
            emoji = "💿"
            detail = f" — {a.get('artistName', '')}"
        elif "playlist" in t:
            emoji = "📋"
            detail = ""
        elif "station" in t:
            emoji = "📻"
            detail = ""
        else:
            emoji = "🎵"
            detail = ""

        lines.append(f"  {i}. {emoji} {name}{detail} | ID: {pid}")

    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Tool: get_recommendations                                          #
# ------------------------------------------------------------------ #


@mcp.tool()
async def get_recommendations(limit: int = 5) -> str:
    """Get personalised Apple Music recommendations.

    Args:
        limit: Number of recommendation groups to return, 1–10 (default 5).
    """
    client = _get_client()
    data = await client.get(
        "/me/recommendations",
        params={"limit": min(max(1, limit), 10)},
    )
    recs = data.get("data", [])

    if not recs:
        return "No recommendations available right now."

    lines = ["🎯 Personalised Recommendations:\n"]
    for rec in recs:
        a = rec.get("attributes", {})
        title_obj = a.get("title", {})
        title = (
            title_obj.get("stringForDisplay", "")
            if isinstance(title_obj, dict)
            else str(title_obj)
        ) or "Recommendation"
        lines.append(f"\n📌 {title}")

        contents = rec.get("relationships", {}).get("contents", {}).get("data", [])
        for i, item in enumerate(contents[:6], 1):
            ia = item.get("attributes", {})
            it = item.get("type", "")
            iid = item.get("id", "?")
            name = ia.get("name", "?")
            if "album" in it:
                lines.append(f"  {i}. 💿 {name} — {ia.get('artistName', '')} | ID: {iid}")
            elif "playlist" in it:
                lines.append(f"  {i}. 📋 {name} | ID: {iid}")
            else:
                lines.append(f"  {i}. 🎵 {name} | ID: {iid}")

    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
