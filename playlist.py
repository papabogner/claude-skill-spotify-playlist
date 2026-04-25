#!/usr/bin/env python3
"""
Spotify playlist builder — exact tracks from a list/URLs.

Usage:
    playlist.py --name "My Playlist" --input tracks.txt [--public] [--description "..."]
    cat tracks.txt | playlist.py --name "My Playlist"

Input format (one entry per line, blank lines and # comments ignored):
    Artist - Track Name           # plain search
    Track Name by Artist          # plain search
    https://open.spotify.com/track/xxxxx   # direct Spotify track URL
    https://youtu.be/xxxxx        # YouTube URL → title → search
    https://www.youtube.com/watch?v=xxx
    spotify:track:xxxxx           # Spotify URI

Credentials read from ~/.config/spotify-skill/credentials.json:
    {"client_id": "...", "client_secret": "...", "redirect_uri": "http://localhost:8888/callback"}

First run opens browser for OAuth. Token cached at ~/.config/spotify-skill/token.json.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

CONFIG_DIR = Path.home() / ".config" / "spotify-skill"
CREDS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_CACHE = CONFIG_DIR / "token.json"
SCOPE = "playlist-modify-private playlist-modify-public"

SPOTIFY_TRACK_RE = re.compile(r"(?:open\.spotify\.com/track/|spotify:track:)([A-Za-z0-9]+)")
URL_RE = re.compile(r"^https?://")


def load_creds():
    if not CREDS_FILE.exists():
        sys.exit(
            f"Missing {CREDS_FILE}\n"
            "Create a Spotify app at https://developer.spotify.com/dashboard\n"
            "Add redirect URI http://127.0.0.1:8888/callback, then write:\n"
            '  {"client_id": "...", "client_secret": "...", "redirect_uri": "http://127.0.0.1:8888/callback"}'
        )
    return json.loads(CREDS_FILE.read_text())


def get_client():
    c = load_creds()
    auth = SpotifyOAuth(
        client_id=c["client_id"],
        client_secret=c["client_secret"],
        redirect_uri=c.get("redirect_uri", "http://127.0.0.1:8888/callback"),
        scope=SCOPE,
        cache_path=str(TOKEN_CACHE),
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth)


def parse_input(text):
    entries = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    return entries


def youtube_title(url):
    try:
        out = subprocess.check_output(
            ["yt-dlp", "--get-title", "--no-playlist", url],
            stderr=subprocess.DEVNULL, timeout=30,
        ).decode().strip()
        # Strip common noise
        out = re.sub(r"\s*\((?:Official|Music|Lyric|HD|HQ|Audio|Video|MV)[^)]*\)", "", out, flags=re.I)
        out = re.sub(r"\s*\[(?:Official|Music|Lyric|HD|HQ|Audio|Video|MV)[^\]]*\]", "", out, flags=re.I)
        return out.strip()
    except Exception as e:
        return None


def resolve_entry(sp, entry):
    """Return (track_id, label) or (None, label) if not found."""
    # Direct Spotify
    m = SPOTIFY_TRACK_RE.search(entry)
    if m:
        tid = m.group(1)
        try:
            t = sp.track(tid)
            return tid, f"{t['artists'][0]['name']} - {t['name']}"
        except Exception:
            return None, entry

    # YouTube/other URL → resolve title
    query = entry
    if URL_RE.match(entry):
        title = youtube_title(entry)
        if not title:
            return None, entry
        query = title

    # Try strict "Artist - Track" parsing first
    if " - " in query and not URL_RE.match(entry):
        artist, track = query.split(" - ", 1)
        strict = f'artist:"{artist.strip()}" track:"{track.strip()}"'
        res = sp.search(q=strict, type="track", limit=1)
        items = res.get("tracks", {}).get("items", [])
        if items:
            t = items[0]
            return t["id"], f"{t['artists'][0]['name']} - {t['name']}"
        # Looser: artist:"X" + track keywords
        loose = f'artist:"{artist.strip()}" {track.strip()}'
        res = sp.search(q=loose, type="track", limit=1)
        items = res.get("tracks", {}).get("items", [])
        if items:
            t = items[0]
            # Verify artist actually matches (case-insensitive substring)
            if artist.strip().lower() in t["artists"][0]["name"].lower() or \
               t["artists"][0]["name"].lower() in artist.strip().lower():
                return t["id"], f"{t['artists'][0]['name']} - {t['name']}"

    # Fallback: plain free search
    res = sp.search(q=query, type="track", limit=1)
    items = res.get("tracks", {}).get("items", [])
    if not items:
        return None, query
    t = items[0]
    return t["id"], f"{t['artists'][0]['name']} - {t['name']}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Playlist name")
    p.add_argument("--input", help="Path to text file (default: stdin)")
    p.add_argument("--description", default="")
    p.add_argument("--public", action="store_true", help="Public playlist (default private)")
    args = p.parse_args()

    text = Path(args.input).read_text() if args.input else sys.stdin.read()
    entries = parse_input(text)
    if not entries:
        sys.exit("No entries found in input.")

    sp = get_client()
    me = sp.me()
    print(f"Authenticated as {me['display_name']} ({me['id']})", file=sys.stderr)

    track_ids, found, missing = [], [], []
    for entry in entries:
        tid, label = resolve_entry(sp, entry)
        if tid:
            track_ids.append(tid)
            found.append(label)
            print(f"  ✓ {label}", file=sys.stderr)
        else:
            missing.append(entry)
            print(f"  ✗ NOT FOUND: {entry}", file=sys.stderr)

    if not track_ids:
        sys.exit("No tracks resolved. Aborting.")

    pl = sp._post("me/playlists", payload={
        "name": args.name,
        "public": args.public,
        "description": args.description,
    })
    # Add in chunks of 100 (Spotify limit)
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(pl["id"], track_ids[i:i + 100])

    print(json.dumps({
        "playlist_url": pl["external_urls"]["spotify"],
        "playlist_id": pl["id"],
        "added": len(track_ids),
        "missing": missing,
    }, indent=2))


if __name__ == "__main__":
    main()
