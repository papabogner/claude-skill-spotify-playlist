# spotify-playlist — Claude Code Skill

A Claude Code skill that builds Spotify playlists from an explicit track list — paste a list, share YouTube/Spotify URLs, or drop a text file. Claude searches each entry and creates the playlist with exact matches.

## What it does

- Accepts track lists in any format: `Artist - Track`, plain search queries, Spotify URLs, YouTube URLs
- Searches Spotify for each entry using strict artist+track matching
- Creates the playlist in your account
- Reports any tracks not found

## Install

```bash
# Copy skill to your Claude skills directory
cp -r spotify-playlist ~/.claude/skills/
```

Or clone this repo and symlink.

## One-time Setup (~5 min)

**1. Create a free Spotify Developer App**

Go to https://developer.spotify.com/dashboard → "Create app"
- Name: anything (e.g. "Claude Playlist Builder")
- Redirect URI: `http://127.0.0.1:8888/callback`
- APIs: check "Web API"

**2. Add yourself as a user**

In your app → Settings → User Management → add your Spotify account email.
(Required while app is in Development Mode — supports up to 25 users.)

**3. Save credentials**

```bash
mkdir -p ~/.config/spotify-skill
cat > ~/.config/spotify-skill/credentials.json << 'EOF'
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://127.0.0.1:8888/callback"
}
EOF
chmod 600 ~/.config/spotify-skill/credentials.json
```

**4. Install Python dependency**

```bash
pip install spotipy
```

**5. First run** — browser opens once for Spotify authorization. Token is cached, all future runs are headless.

## Usage

Once installed, just tell Claude:

> "Mach mir eine Playlist 'Sommer 2026' aus dieser Liste: Daft Punk - Around the World, Justice - D.A.N.C.E., ..."

> "Create a playlist called 'Road Trip' from these YouTube links: ..."

> "Playlist aus dieser Datei: /path/to/tracks.txt"

Claude handles the rest.

## Input format

One entry per line — mix formats freely:

```
Daft Punk - Around the World
Justice - D.A.N.C.E.
https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
spotify:track:7ouMYWpwJ422jRcDASZB7P
https://youtu.be/dQw4w9WgXcQ
Bohemian Rhapsody
# this is a comment, ignored
```

YouTube URLs require `yt-dlp` installed (`pip install yt-dlp`).

## Direct CLI usage

```bash
python3 ~/.claude/skills/spotify-playlist/playlist.py \
  --name "My Playlist" \
  --input tracks.txt \
  --description "optional description" \
  --public   # omit for private
```

## Privacy

Your credentials and tokens are stored **only on your machine** at `~/.config/spotify-skill/`. Nothing is shared or uploaded.

## Requirements

- Python 3.8+
- `spotipy` (`pip install spotipy`)
- `yt-dlp` for YouTube URLs (optional, `pip install yt-dlp`)
- Free Spotify account (no Premium required for playlist creation)
