# mcp-apple-music 🎵

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol) server** that gives Claude full access to your Apple Music account — search the catalog, browse your personal library, manage playlists, and explore your listening history and recommendations.

> **Ask Claude things like:**
> - *"Based on what I've been listening to lately, recommend 15 songs I don't have yet and add them to a new playlist"*
> - *"Show me all my playlists and tell me which artists appear most"*
> - *"Search for albums by Nick Cave and add my three favourites to a playlist called Dark Picks"*

---

## Features

| Tool | Description |
|---|---|
| `search_catalog` | Search Apple Music catalog (songs, albums, artists, playlists) |
| `search_library` | Search within your personal library |
| `get_library_songs` | List songs saved in your library (paginated) |
| `get_library_albums` | List albums in your library (paginated) |
| `get_library_artists` | List artists in your library |
| `get_library_playlists` | List all your playlists with IDs |
| `get_playlist_tracks` | Get tracks inside a specific playlist |
| `create_playlist` | Create a new playlist |
| `add_tracks_to_playlist` | Add songs to a playlist (library or catalog tracks) |
| `get_recently_played` | See recently played albums/playlists/stations |
| `get_recommendations` | Get personalised Apple Music picks |

---

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An **Apple Developer account** (free tier is fine) with a MusicKit key
- An active **Apple Music subscription**

---

## Setup

### 1. Create a MusicKit Key

1. Go to [developer.apple.com](https://developer.apple.com) → **Certificates, Identifiers & Profiles**
2. Under **Keys**, click **+** to create a new key
3. Give it any name, enable **MusicKit**, and click **Continue → Register**
4. **Download** the `.p8` file — you can only download it once, keep it safe!
5. Note your **Key ID** (e.g. `ABC123DEF4`) and your **Team ID** (found under *Membership Details*)

> ⚠️ The Key ID is the alphanumeric code shown next to the key name — **not** the filename of the `.p8` file.

### 2. Clone and install

```bash
git clone https://github.com/marioinghilleri/mcp-apple-music
cd mcp-apple-music

# with uv (recommended)
uv sync

# or with pip
pip install -e .
```

### 3. Run the one-time setup wizard

```bash
# with uv
uv run mcp-apple-music-setup

# or directly
python -m mcp_apple_music.setup
```

The wizard will ask for your **Team ID**, **Key ID**, and the path to your `.p8` file. It then opens a browser page where you click **"Authorise Apple Music"** — this uses Apple's official MusicKit JS to obtain your Music User Token, which is stored securely at `~/.config/mcp-apple-music/config.json` (file permissions: `600`).

### 4. Add to Claude Desktop

Open your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apple-music": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/mcp-apple-music",
        "mcp-apple-music"
      ]
    }
  }
}
```

Restart Claude Desktop — you should see the apple-music tools available in the toolbar.

---

## How it works

Apple Music requires two separate tokens:

- **Developer Token** — a JWT you sign locally with your `.p8` private key. Valid up to 6 months; the server regenerates it automatically before expiry. Your key never leaves your machine.
- **Music User Token** — obtained once via MusicKit JS OAuth in the browser (the setup wizard handles this). Stored locally at `~/.config/mcp-apple-music/config.json`.

```
Your .p8 key  ──►  Developer Token (JWT, auto-renewed)  ─┐
                                                           ├──► Apple Music API
Browser OAuth ──►  Music User Token (stored locally)    ─┘
```

> ⚠️ **Playback control** (play/pause/skip) is not available via Apple's REST API. It requires native MusicKit frameworks (iOS/macOS app) or MusicKit JS running in a browser context.

---

## Project structure

```
mcp-apple-music/
├── src/
│   └── mcp_apple_music/
│       ├── __init__.py
│       ├── auth.py      — Developer Token generation + User Token management
│       ├── client.py    — Async HTTP client for api.music.apple.com
│       ├── server.py    — FastMCP server with all 11 tools
│       └── setup.py     — One-time setup wizard (browser-based OAuth)
├── config.example.json  — Example config structure (no secrets)
├── pyproject.toml
└── README.md
```

---

## Example prompts

Once connected, you can ask Claude:

```
"What have I been listening to this week? Based on that, find 10 songs
 I don't own yet that I'd probably enjoy and create a playlist with them."

"Search for all albums by Joni Mitchell and tell me which ones
 I already have in my library."

"List my playlists, pick the one that looks most like a workout mix,
 and add 5 high-energy songs from the catalog to it."

"Create a playlist called 'Rainy Sunday' with the 10 most mellow tracks
 you can find from my library."
```

---

## Authors

Built by **[Mario Inghilleri](https://github.com/marioinghilleri)** and **[Claude](https://claude.ai)** (Anthropic) as part of a personal MCP ecosystem for Claude Desktop.

This project was conceived, designed, debugged, and shipped entirely through a collaborative conversation between Mario and Claude — from API research and auth flow design, through the setup wizard, to live testing with a real Apple Music library.

Contributions, issues and PRs are welcome!

---

## License

[MIT](LICENSE) — use it, fork it, build on it.
