#!/usr/bin/env python3
"""
Photo → Spotify Playlist

NOT called directly. Claude analyzes the image and calls this script with
extracted vibe, mood, setting, colors, and era as text descriptions.

Usage (called by Claude after image analysis):
    photo_playlist.py --name "Playlist Name" --vibe "..." [--era "1970s"] [--bpm slow|medium|fast] [--public]
"""
import argparse, json, sys
from pathlib import Path
from playlist import get_client, resolve_entry

VIBE_TO_QUERIES = {
    # Claude generates these dynamically — this is just fallback reference
}

def vibe_to_search_queries(vibe: str, era: str, bpm: str, sp):
    """
    Build 20-30 search queries from a vibe description.
    Returns list of (query, rationale) tuples.
    """
    # Use Spotify's recommendation endpoint seeded by genre + mood
    # First: map vibe words to Spotify genre seeds
    genre_map = {
        "warm": ["soul", "funk", "bossa-nova"],
        "cold": ["ambient", "post-rock", "minimal-techno"],
        "melancholic": ["sad", "indie", "singer-songwriter"],
        "energetic": ["dance", "house", "hip-hop"],
        "romantic": ["romance", "french", "bossa-nova"],
        "dark": ["gothic", "metal", "industrial"],
        "sunny": ["pop", "reggae", "afrobeat"],
        "nostalgic": ["oldies", "soul", "classic-rock"],
        "urban": ["hip-hop", "r-n-b", "trip-hop"],
        "nature": ["folk", "ambient", "new-age"],
        "party": ["edm", "pop", "latin"],
        "focus": ["study", "classical", "minimal-techno"],
        "melancholy": ["blues", "indie", "folk"],
        "dreamy": ["dream-pop", "shoegaze", "ambient"],
        "aggressive": ["metal", "punk", "hardcore"],
        "peaceful": ["ambient", "acoustic", "classical"],
        "dramatic": ["classical", "opera", "film-score"],
        "playful": ["pop", "indie-pop", "children"],
        "mysterious": ["darkwave", "trip-hop", "ambient"],
        "spiritual": ["gospel", "world-music", "new-age"],
    }

    bpm_map = {
        "slow": (40, 80),
        "medium": (80, 120),
        "fast": (120, 180),
    }

    # Find matching genres from vibe text
    vibe_lower = vibe.lower()
    matched_genres = []
    for keyword, genres in genre_map.items():
        if keyword in vibe_lower:
            matched_genres.extend(genres)

    if not matched_genres:
        matched_genres = ["pop", "indie", "soul"]  # safe defaults

    # Deduplicate and limit
    matched_genres = list(dict.fromkeys(matched_genres))[:5]

    # Build recommendations request
    params = {
        "seed_genres": matched_genres[:5],
        "limit": 30,
    }

    if era:
        decade_map = {
            "60": (1960, 1969), "70": (1970, 1979), "80": (1980, 1989),
            "90": (1990, 1999), "00": (2000, 2009), "10": (2010, 2019), "20": (2020, 2029),
        }
        for key, (start, end) in decade_map.items():
            if key in era:
                params["target_release_year_start"] = start
                break

    if bpm in bpm_map:
        lo, hi = bpm_map[bpm]
        params["target_tempo"] = (lo + hi) // 2
        params["min_tempo"] = lo
        params["max_tempo"] = hi

    try:
        recs = sp.recommendations(**params)
        return [(t["id"], f"{t['artists'][0]['name']} - {t['name']}") for t in recs["tracks"]]
    except Exception as e:
        print(f"Recommendations failed: {e}", file=sys.stderr)
        # Fallback: search by vibe keywords
        queries = [f"{g} {era or ''} music".strip() for g in matched_genres[:5]]
        results = []
        for q in queries:
            res = sp.search(q=q, type="track", limit=6)
            for t in res.get("tracks", {}).get("items", []):
                results.append((t["id"], f"{t['artists'][0]['name']} - {t['name']}"))
        return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--vibe", required=True, help="Claude's vibe analysis of the image")
    p.add_argument("--era", default="", help="e.g. '1970s', '90s'")
    p.add_argument("--bpm", default="medium", choices=["slow", "medium", "fast"])
    p.add_argument("--description", default="")
    p.add_argument("--public", action="store_true")
    args = p.parse_args()

    sp = get_client()
    me = sp.me()
    print(f"Authenticated as {me['display_name']}", file=sys.stderr)
    print(f"Vibe: {args.vibe}", file=sys.stderr)
    print(f"Era: {args.era or 'any'} | BPM: {args.bpm}", file=sys.stderr)

    tracks = vibe_to_search_queries(args.vibe, args.era, args.bpm, sp)

    if not tracks:
        sys.exit("No tracks found for this vibe.")

    # Deduplicate
    seen, unique = set(), []
    for tid, label in tracks:
        if tid not in seen:
            seen.add(tid)
            unique.append((tid, label))
            print(f"  ✓ {label}", file=sys.stderr)

    ids = [tid for tid, _ in unique]
    pl = sp._post("me/playlists", payload={
        "name": args.name,
        "public": args.public,
        "description": args.description or f"Generated from photo vibe: {args.vibe[:100]}",
    })

    for i in range(0, len(ids), 100):
        sp.playlist_add_items(pl["id"], ids[i:i + 100])

    print(json.dumps({
        "playlist_url": pl["external_urls"]["spotify"],
        "playlist_id": pl["id"],
        "added": len(ids),
        "vibe": args.vibe,
    }, indent=2))


if __name__ == "__main__":
    main()
