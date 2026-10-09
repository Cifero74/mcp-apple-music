# Changelog

## [1.2.0] — 2026-10-09

### Added
- Favorites support: `favorite_song`, `unfavorite_song` and `get_song_favorite_status` (catalog songs, via `/v1/me/ratings/songs`).

### Fixed
- Setup wizard: calls `music.unauthorize()` before `authorize()`, so MusicKit JS no longer reuses a cached, revoked user token (API 403 "Invalid authentication").
- Setup wizard: uses `ThreadingHTTPServer`, so a second browser tab no longer hangs.

## [1.1.0] — 2026-09-30

### Added
- `get_playlist_tracks` supports `offset` pagination and `fetch_all=True` to read playlists longer than 100 tracks (#7, thanks @nate-thegrate; supersedes #9, thanks @darthzen).

### Fixed
- Pin `mcp` to `<2`: mcp 2.x renamed FastMCP and fresh installs failed at startup.
- `get_recently_played` clamps `limit` to 10, the Apple API maximum (#10, thanks @darthzen).
- Pagination follows Apple's relative `next` links correctly.
- Faster startup: PyJWT/cryptography are imported lazily, avoiding MCP init timeouts (#8, thanks @townsendjs).

### Docs
- README: a paid Apple Developer Program membership is required for MusicKit keys (#5, thanks @alexbazanb).
- README: fixed the clone URL.

## [1.0.1] — 2026-03

- Package renamed to `mcp-apple-music-server` on PyPI; published to the official MCP Registry.

## [1.0.0] — 2026-03

- First public release: 11 tools for catalog search, library and playlists.
