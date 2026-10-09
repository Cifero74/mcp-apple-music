# CLAUDE.md — mcp-apple-music

MCP server for the Apple Music REST API (catalog search, library, playlists, favorites). Published on PyPI as `mcp-apple-music-server` and in the MCP Registry as `io.github.Cifero74/mcp-apple-music`.

## Stack
- Python 3.10+, managed with `uv` (build backend: hatchling)
- FastMCP (`mcp[cli]>=1.0.0,<2`), httpx (async), PyJWT + cryptography (ES256 developer token)
- No test suite and no lint config in the repo

## Structure (`src/mcp_apple_music/`)
- `auth.py`: `AppleMusicAuth`. It signs the developer token from the `.p8` key and loads the Music User Token, either from `~/.config/mcp-apple-music/config.json` or from env vars (`APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY`, `APPLE_MUSIC_USER_TOKEN`, `APPLE_STOREFRONT`)
- `client.py`: `AppleMusicClient`, a thin async wrapper (`get`/`post`/`put`/`delete`/`get_url`/`get_all_pages`) over `https://api.music.apple.com/v1`
- `server.py`: the FastMCP app and all `@mcp.tool()` async tools; entry point `mcp-apple-music`
- `setup.py`: the setup wizard (`mcp-apple-music-setup`). It serves a local MusicKit JS page so the user can log in and get a Music User Token

## Verify recipe
1. `uv run python -m compileall -q src`
2. `uvx ruff check src`. Baseline as of ruff 0.16.10: 8 pre-existing findings (7× UP045 `Optional[X]`, 1× BLE001 in `setup.py`), all from default rules, since there's no ruff config. Until they're cleaned up, the gate is "no new findings".
3. Live smoke test. Call the async tools directly (the `@mcp.tool()` decorator returns the plain function):
   ```sh
   perl -e 'alarm 60; exec @ARGV' uv run python -c '
   import asyncio
   from mcp_apple_music import server as s
   async def main():
       print(await s.search_catalog("Lauryn Hill", types="songs", limit=2))
       print(await s.get_song_favorite_status("1276760751"))
   asyncio.run(main())
   '
   ```
   Use read-only calls only. Never change Mario's real favorites. To test write tools, use a throwaway song (e.g. `1276760752`, not favorited) and restore its original state afterwards.

## Gotchas
- `GET /me/ratings/songs?ids=...` returns 200 with empty `data` for unrated songs; that response means "not favorited", not an error.
- Ratings value `1` = favorite (the star in Apple Music); `-1` = dislike.
- A 403 "Invalid authentication" on `/me/*` while catalog calls work means the Music User Token is dead. Fix: Mario reruns `uv run mcp-apple-music-setup` → `r` and logs in himself. Don't try to work around it in code.
- MusicKit JS caches the user token in the browser. That's why the wizard calls `music.unauthorize()` before `authorize()` and uses `ThreadingHTTPServer` (with plain `HTTPServer`, a second tab hangs). Keep both.
- The REST API has no playback control (play/pause/queue), so don't add tools for it.
- Never print, cat or log `~/.config/mcp-apple-music/config.json` or the `.p8` key. Also keep the repo-local `config.json` and `.mcpregistry_*` token files out of output and commits (they're gitignored; don't `git add -f`).
- `timeout` isn't installed on this Mac. Use `perl -e 'alarm N; exec @ARGV' <cmd>`.

## Releases
- Keep the version in sync in `pyproject.toml`, in both `version` fields of `server.json`, and in `uv.lock`.
- Add a `CHANGELOG.md` entry for every release.
- Never publish to PyPI, create a GitHub release, or publish to the MCP Registry without Mario's explicit OK.
