---
name: spotify-playlist
description: Use when the user wants to create a Spotify playlist from an explicit list of tracks, a text file, YouTube URLs, or Spotify track links. Searches each entry on Spotify, builds the playlist with exact matches, and reports anything not found. Triggers on "spotify playlist", "mach mir ne playlist", "playlist aus dieser liste", "tracks zu playlist", or any URL/track-list-to-playlist request.
---

# Spotify Playlist Builder

Builds a Spotify playlist from an explicit input list — not the generative MCP `create_playlist` (which guesses tracks). Uses Spotify Web API via spotipy with the user's own OAuth token.

## When to use

- User provides a list of tracks (in chat, as a file, or pasted) and wants them as a Spotify playlist
- User shares YouTube/Spotify URLs and wants them collected
- User says "create playlist with these songs" / "mach playlist aus..."

**Do NOT use** the Spotify MCP `create_playlist` for these — it's prompt-based and will swap/miss tracks.

## One-time setup

If `~/.config/spotify-skill/credentials.json` does not exist:

1. Tell the user to create a Spotify app at https://developer.spotify.com/dashboard
2. Settings → add Redirect URI: `http://127.0.0.1:8888/callback` (Spotify rejects `localhost` as insecure; use the IP)
3. Copy Client ID + Client Secret
4. Write `~/.config/spotify-skill/credentials.json`:
   ```json
   {"client_id": "...", "client_secret": "...", "redirect_uri": "http://127.0.0.1:8888/callback"}
   ```
5. First run will open the browser for authorization (one time). Token caches at `~/.config/spotify-skill/token.json`.

## Usage

Write the user's list to a temp file, then run:

```bash
python3 ~/.claude/skills/spotify-playlist/playlist.py \
  --name "Playlist Name" \
  --input /tmp/tracks.txt \
  --description "optional"
```

Add `--public` for a public playlist (default: private).

You can also pipe via stdin:
```bash
cat tracks.txt | python3 ~/.claude/skills/spotify-playlist/playlist.py --name "..."
```

## Input format

One entry per line, blanks and `#` comments ignored. Mix freely:

```
Daft Punk - Around the World
https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
spotify:track:7ouMYWpwJ422jRcDASZB7P
https://youtu.be/dQw4w9WgXcQ
Bohemian Rhapsody by Queen
```

- Spotify URLs/URIs → used directly
- Other URLs → `yt-dlp --get-title` → searched on Spotify
- Plain text → searched as-is, top match wins

## Output

JSON to stdout with `playlist_url`, `added` count, and `missing` list. Per-track ✓/✗ to stderr.

**Always show the user:**
- The playlist URL (clickable)
- The list of any missing tracks so they can correct/retry

## Common issues

| Problem | Fix |
|---------|-----|
| `Missing credentials.json` | Run setup above |
| Wrong cover/version picked | Make the input line more specific: include album or year |
| YouTube title messy | Strip "(Official Video)" etc. or replace with `Artist - Track` plain text |
| Token expired | Delete `~/.config/spotify-skill/token.json`, re-run |
