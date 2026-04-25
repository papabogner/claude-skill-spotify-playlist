#!/usr/bin/env python3
"""
Vinyl → Spotify Playlist

NOT called directly. Claude reads a photo of vinyl records/shelf and extracts
artist + album names visually, then calls this script with the list.

Usage (called by Claude after image analysis):
    vinyl_scanner.py --records "Artist1 - Album1\nArtist2 - Album2\n..." --name "My Vinyl Collection"

Or from a text file:
    vinyl_scanner.py --input records.txt --name "My Vinyl Collection" [--mode album|tracks|both]

Modes:
  album:  add the full album to the playlist (up to 50 tracks per album)
  tracks: add only the most popular track from each album (default)
  both:   add 3 most popular tracks per album
"""
import argparse, json, re, sys
from pathlib import Path
from playlist import get_client


def normalize_entry(entry: str) -> str:
    """Lowercase, strip punctuation for dedup comparison."""
    return re.sub(r'[^\w\s]', '', entry.lower()).strip()


def find_album_tracks(sp, artist: str, album: str, mode: str) -> list[tuple[str, str]]:
    """Search for an album and return its tracks based on mode."""
    query = f'artist:"{artist}" album:"{album}"'
    res = sp.search(q=query, type="album", limit=3)
    albums = res.get("albums", {}).get("items", [])

    if not albums:
        # Fuzzy fallback
        query = f"{artist} {album}"
        res = sp.search(q=query, type="album", limit=3)
        albums = res.get("albums", {}).get("items", [])

    if not albums:
        return []

    album_obj = albums[0]
    album_id = album_obj["id"]
    album_name = album_obj["name"]
    artist_name = album_obj["artists"][0]["name"]

    # Get tracks from album
    tracks_res = sp.album_tracks(album_id, limit=50)
    all_tracks = tracks_res.get("items", [])

    if mode == "tracks":
        # Most popular single track
        if all_tracks:
            t = all_tracks[0]  # usually ordered by track number; get via full track for popularity
            # Fetch full track objects to get popularity
            ids = [t["id"] for t in all_tracks[:20]]
            full = sp.tracks(ids)["tracks"]
            best = max(full, key=lambda x: x.get("popularity", 0))
            return [(best["id"], f"{artist_name} - {album_name} / {best['name']}")]

    elif mode == "both":
        ids = [t["id"] for t in all_tracks[:20]]
        full = sp.tracks(ids)["tracks"]
        top3 = sorted(full, key=lambda x: x.get("popularity", 0), reverse=True)[:3]
        return [(t["id"], f"{artist_name} - {t['name']}") for t in top3]

    else:  # album — all tracks
        return [(t["id"], f"{artist_name} - {t['name']}") for t in all_tracks]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--records", help="Newline-separated 'Artist - Album' list")
    p.add_argument("--input", help="Path to text file with records")
    p.add_argument("--mode", default="tracks", choices=["album", "tracks", "both"],
                   help="tracks=1 hit per album, both=3 per album, album=full album")
    p.add_argument("--dedupe", action="store_true",
                   help="Remove duplicate entries (useful when merging frames from a video scan)")
    p.add_argument("--public", action="store_true")
    args = p.parse_args()

    if args.input:
        raw = Path(args.input).read_text()
    elif args.records:
        raw = args.records
    else:
        raw = sys.stdin.read()

    entries = [l.strip() for l in raw.splitlines() if l.strip() and not l.startswith("#")]

    if args.dedupe:
        seen_norm, deduped = set(), []
        for e in entries:
            n = normalize_entry(e)
            if n not in seen_norm:
                seen_norm.add(n)
                deduped.append(e)
        removed = len(entries) - len(deduped)
        if removed:
            print(f"Deduped: removed {removed} duplicate entries", file=sys.stderr)
        entries = deduped
    if not entries:
        sys.exit("No records found in input.")

    sp = get_client()
    me = sp.me()
    print(f"Authenticated as {me['display_name']}", file=sys.stderr)
    print(f"Scanning {len(entries)} records (mode: {args.mode})...", file=sys.stderr)

    track_ids, found, missing = [], [], []

    for entry in entries:
        if " - " in entry:
            artist, album = entry.split(" - ", 1)
        else:
            artist, album = entry, entry

        tracks = find_album_tracks(sp, artist.strip(), album.strip(), args.mode)
        if tracks:
            for tid, label in tracks:
                track_ids.append(tid)
                found.append(label)
            print(f"  ✓ {entry} ({len(tracks)} track{'s' if len(tracks) > 1 else ''})", file=sys.stderr)
        else:
            missing.append(entry)
            print(f"  ✗ NOT FOUND: {entry}", file=sys.stderr)

    if not track_ids:
        sys.exit("No tracks resolved.")

    pl = sp._post("me/playlists", payload={
        "name": args.name,
        "public": args.public,
        "description": f"Vinyl collection — {len(entries)} records, {len(track_ids)} tracks",
    })

    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(pl["id"], track_ids[i:i + 100])

    print(json.dumps({
        "playlist_url": pl["external_urls"]["spotify"],
        "playlist_id": pl["id"],
        "records_processed": len(entries),
        "tracks_added": len(track_ids),
        "missing": missing,
    }, indent=2))


if __name__ == "__main__":
    main()
