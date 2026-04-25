# spotify-playlist

**Turn anything into a Spotify playlist.**

A Claude Code skill that builds Spotify playlists from whatever you throw at it — a list of tracks, a photo, a shelf of vinyl, a video pan across your collection, a message you want hidden in song titles, a film, an emotion. Claude does the analysis. Spotify gets the playlist. You get the link.

```
   ╔══════════════════════════════════════════════════╗
   ║    LIST   PHOTO   VINYL   MESSAGE   FILM   LETTER   ║
   ║      └──────┴───────┴────┬─────┴──────┴──────┘      ║
   ║                          ▼                          ║
   ║                  ▶ SPOTIFY PLAYLIST                 ║
   ╚══════════════════════════════════════════════════╝
```

---

## Six Modes

### 🎵 Track List → Playlist
Drop the list. Get the playlist.

Paste tracks, share Spotify URLs, drop YouTube links — mix freely. Claude searches each entry with strict artist+track matching, builds the playlist, and tells you what couldn't be found.

```
Daft Punk - Around the World
https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
https://youtu.be/dQw4w9WgXcQ
Bohemian Rhapsody
```

---

### 📸 Photo → Playlist
*A photo is a vibe. A vibe is a playlist.*

Send a photo. Claude reads the mood, era, energy, and atmosphere — then builds a playlist that sounds like the picture feels. Sunset on a balcony hits different than a neon street at 2am.

---

### 💿 Vinyl Shelf → Spotify
*Your record collection, digitized.*

One photo of a few records, multiple shots of the whole shelf, or a video panning along your collection — Claude reads every cover, deduplicates across frames, and turns the lot into a Spotify playlist. Pick most-popular track per album, top 3, or the full album.

---

### 💬 Playlist with a Message
*Make the music say it.*

Song titles, read top-to-bottom, spell out your message. Want the playlist to say "I LOVE YOU" or "HAPPY BIRTHDAY MARCO"? It finds the tracks. If a word can't be matched, it suggests slight edits that would work.

---

### 🎬 Film → Playlist
*Goodfellas in 30 tracks.*

Name a film. Claude knows the era, the mood, the emotional arc — and builds a playlist that captures the *feeling* of the film, not just the soundtrack.

---

### 💌 Letter → Playlist
*Words you can't send. Songs you can.*

Write the message. Claude translates the emotion into a sequence of songs that say what you couldn't. For when "I miss you" needs more than three syllables.

---

## Install

```bash
git clone https://github.com/papabogner/claude-skill-spotify-playlist ~/.claude/skills/spotify-playlist
bash ~/.claude/skills/spotify-playlist/setup.sh
```

The setup script installs dependencies, asks for your Spotify Developer credentials, and writes them to `~/.config/spotify-skill/credentials.json`. Nothing leaves your machine.

## One-time Spotify Setup (~5 min)

1. Create a free Spotify Developer App at https://developer.spotify.com/dashboard
2. Add Redirect URI: `http://127.0.0.1:8888/callback`
3. Settings → User Management → add your own Spotify email (Development Mode allows up to 25 users without Spotify approval)
4. Copy Client ID + Client Secret into the setup script when asked
5. First run opens your browser once for OAuth. Token is cached.

## Privacy

Your credentials, OAuth token, and playlists live entirely on your machine and your Spotify account. The skill makes API calls directly from your laptop to Spotify — no proxy, no telemetry, no third party.

## Requirements

- Python 3.8+
- `spotipy` — Spotify API client
- `yt-dlp` — for YouTube URL support (optional)
- `ffmpeg` — for video frame extraction (optional, for vinyl video mode)
- Free Spotify account (Premium not required to create playlists)

## How it works

The scripts in this repo are dumb — they handle Spotify API calls. The intelligence lives in Claude. When you send a photo, Claude analyzes it. When you send a video, Claude extracts and analyzes frames. When you say "playlist that says I miss you", Claude translates emotion into a vibe descriptor. The scripts just execute on the structured output.

This is what makes it work without a hosted backend: Claude is the vision model, the curator, the translator. You bring your own Spotify keys.

## License

MIT
