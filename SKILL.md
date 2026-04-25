---
name: spotify-playlist
description: Use when the user wants to build a Spotify playlist from any source — an explicit track list (text, file, Spotify URLs, YouTube URLs), a photo whose mood should become a playlist, a vinyl shelf scanned via photo or video, a hidden message that song titles should spell out, a film whose vibe should be captured, or an emotional message translated into music. Triggers on "spotify playlist", "create playlist", "playlist from these tracks", "playlist from this photo", "vinyl to spotify", "scan my records", "song titles spell", "playlist that says", or any natural request to turn input into a Spotify playlist.
---

# Spotify Playlist — All Modes

Turns anything into a Spotify playlist. Uses the Spotify Web API via spotipy and the user's own OAuth token. Requires `~/.config/spotify-skill/credentials.json`.

## Mode Map

| Trigger | Mode | Script |
|---------|------|--------|
| list of tracks / links | **Standard** | `playlist.py` |
| photo / image | **Photo Vibe** | `photo_playlist.py` |
| vinyl photo / shelf video | **Vinyl Scanner** | `vinyl_scanner.py` |
| "titles spell ..." | **Playlist with a Message** | `message_playlist.py` |
| film name | **Film Vibe** | `photo_playlist.py --vibe` |
| emotional text / letter | **Letter** | `photo_playlist.py --vibe` |

---

## Mode 1 — Standard: Track List

Input: text lines, Spotify URLs, YouTube URLs, or mixed.

```bash
python3 ~/.claude/skills/spotify-playlist/playlist.py \
  --name "Playlist Name" --input /tmp/tracks.txt
```

Input format (one per line, `#` = comment):
```
Daft Punk - Around the World
https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
https://youtu.be/dQw4w9WgXcQ
Bohemian Rhapsody by Queen
```

YouTube URLs require `yt-dlp` (`pip install yt-dlp`).

---

## Mode 2 — Photo / Image → Playlist

User sends a photo. Claude analyzes it and builds a mood playlist.

**Claude's role:**
1. Read the image with the Read tool
2. Extract: overall vibe (2-3 sentences), dominant colors/mood, era/decade if inferable, energy level (slow/medium/fast)
3. Write vibe as a comma-separated descriptor string, e.g.:
   `"warm, melancholic, urban twilight, 1970s soul influence, slow"`
4. Run:

```bash
python3 ~/.claude/skills/spotify-playlist/photo_playlist.py \
  --name "Playlist Name" \
  --vibe "warm, melancholic, urban twilight, 1970s soul" \
  --era "1970s" \
  --bpm slow
```

**BPM:** `slow` / `medium` / `fast`
**Era:** `1960s`, `1970s`, `1980s`, `1990s`, `2000s`, `2010s`, `2020s` (optional)

---

## Mode 3 — Vinyl Collection Scanner

User sends photo(s) of vinyl shelf or a video panning along a collection.

### Single photo (one or many records visible)
1. Read the image
2. Scan systematically left→right, top→bottom
3. List every visible artist + album: `Artist - Album`
4. Write to `/tmp/vinyl_records.txt`
5. Run:

```bash
python3 ~/.claude/skills/spotify-playlist/vinyl_scanner.py \
  --name "My Vinyl Collection" \
  --input /tmp/vinyl_records.txt \
  --mode tracks \
  --dedupe
```

### Multiple photos (folder or list of files)
1. Read each image in sequence
2. Append all recognized records to one list
3. Run with `--dedupe` to remove records visible in multiple photos

### Video (shelf pan, walkthrough)
1. Extract frames with ffmpeg (one frame every 3 seconds):

```bash
mkdir -p /tmp/vinyl_frames
ffmpeg -i /path/to/video.mp4 -vf fps=1/3 /tmp/vinyl_frames/frame_%04d.jpg -y 2>/dev/null
```

2. List the frames: `ls /tmp/vinyl_frames/`
3. Read each frame image with the Read tool
4. Collect all recognized records → write to `/tmp/vinyl_records.txt`
5. Run with `--dedupe` (same cover visible across multiple frames)

**Mode options:**
- `--mode tracks` — 1 most popular track per album (default)
- `--mode both` — 3 most popular tracks per album
- `--mode album` — full album

---

## Mode 4 — Playlist with a Message: Song Titles Spell It Out

User wants song titles to spell out a word, phrase, or sentence.

### Word mode (recommended)
Each WORD in the target text = a song title (or a song starting with that word).

```bash
python3 ~/.claude/skills/spotify-playlist/message_playlist.py \
  --text "I love you" \
  --mode word \
  --name "Secret Message"
```

### Letter mode
First LETTER of each song title spells the text (harder, more misses).

```bash
python3 ~/.claude/skills/spotify-playlist/message_playlist.py \
  --text "MARCO" \
  --mode letter \
  --name "For Marco"
```

Output includes `suggestions` — if a word/letter didn't match perfectly, the script proposes slight text edits that would work. **Always show these to the user** and offer to rebuild with adjusted text.

Example: "I love you" → `love` matched loosely → suggestion: use `adore` instead → ask user if they want to rebuild.

---

## Mode 5 — Film Vibe

Claude interprets the film's emotional arc, era, and genre.

**Claude's role:**
1. Analyze: film era, dominant mood, energy arc (slow build? intense throughout?), cultural context
2. Build vibe string + era
3. Call `photo_playlist.py` same as Mode 2

Example for "Goodfellas":
```bash
python3 ~/.claude/skills/spotify-playlist/photo_playlist.py \
  --name "Goodfellas Vibe" \
  --vibe "swaggering, urban, dangerous elegance, Italian-American cool, high energy with dark undertones" \
  --era "1970s" \
  --bpm medium
```

---

## Mode 6 — Emotional Message / Letter as Playlist

User writes a message or emotional situation. Claude translates it to music.

**Claude's role:**
1. Read the emotional content carefully
2. Extract: core feeling, relational context, energy, resolution (open/closed)
3. Build vibe string that *encodes* the emotion, not just describes it
4. Call `photo_playlist.py`

Example: "I've been missing someone for months and I don't know if they'll come back":
```bash
python3 ~/.claude/skills/spotify-playlist/photo_playlist.py \
  --name "Unsent Letter" \
  --vibe "longing, suspended time, quiet hope, late night introspection, soft melancholy" \
  --bpm slow
```

---

## Setup (one-time)

Credentials at `~/.config/spotify-skill/credentials.json`:
```json
{"client_id": "...", "client_secret": "...", "redirect_uri": "http://127.0.0.1:8888/callback"}
```

Add yourself in Spotify Dashboard → User Management.
First run opens browser once for OAuth. Token cached at `~/.config/spotify-skill/token.json`.

**Install:**
```bash
pip install spotipy yt-dlp
brew install ffmpeg  # for video frame extraction
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 403 Forbidden on playlist create | Add your email in Spotify Dashboard → User Management |
| Token expired | Delete `~/.config/spotify-skill/token.json`, re-run |
| Wrong track matched | Make input line more specific: add year or album |
| Message word not found | Accept suggestion, rebuild with adjusted text |
| ffmpeg not found | `brew install ffmpeg` |
