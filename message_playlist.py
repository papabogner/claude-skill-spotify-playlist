#!/usr/bin/env python3
"""
Playlist with a Message — song titles, read in order, spell out a message.

Two modes:
  word:   each WORD in the target text is a song title (or starts with that word)
  letter: first LETTER of each song title spells the text (harder, often needs suggestions)

Usage:
    message_playlist.py --text "I love you" --mode word --name "Secret Message"
    message_playlist.py --text "HAPPY BIRTHDAY MARCO" --mode word --name "For Marco"
    message_playlist.py --text "SORRY" --mode letter --name "..."
"""
import argparse, json, sys, re
from difflib import SequenceMatcher
from playlist import get_client

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_track_for_word(sp, word: str):
    """Find a track whose title IS the word or STARTS with the word."""
    # Try exact title match first
    for query in [
        f'track:"{word}"',
        f'track:"{word} ',
        word,
    ]:
        res = sp.search(q=query, type="track", limit=10)
        for t in res.get("tracks", {}).get("items", []):
            title = t["name"]
            title_clean = re.sub(r'\s*[\(\[].*?[\)\]]', '', title).strip().lower()
            if title_clean == word.lower():
                return t["id"], f"{t['artists'][0]['name']} - {t['name']}", 1.0
            if title_clean.startswith(word.lower()):
                score = len(word) / len(title_clean)
                return t["id"], f"{t['artists'][0]['name']} - {t['name']}", score

    # Fuzzy: find track with highest title similarity to word
    res = sp.search(q=word, type="track", limit=20)
    best_id, best_label, best_score = None, None, 0.0
    for t in res.get("tracks", {}).get("items", []):
        title = re.sub(r'\s*[\(\[].*?[\)\]]', '', t["name"]).strip()
        score = similarity(word, title.split()[0] if title.split() else title)
        if score > best_score:
            best_score = score
            best_id = t["id"]
            best_label = f"{t['artists'][0]['name']} - {t['name']}"

    return best_id, best_label, best_score


def find_track_for_letter(sp, letter: str):
    """Find a popular track starting with the given letter."""
    res = sp.search(q=letter, type="track", limit=20)
    for t in res.get("tracks", {}).get("items", []):
        if t["name"].upper().startswith(letter.upper()):
            return t["id"], f"{t['artists'][0]['name']} - {t['name']}"
    return None, f"[No track starting with '{letter}']"


def suggest_word_alternatives(word: str) -> list[str]:
    """Suggest synonyms/similar words that might be easier to match."""
    # Simple static map for common hard words — Claude should handle this contextually
    alternatives = {
        "i": ["me", "myself"],
        "a": ["one", "the"],
        "the": ["a", "this"],
        "and": ["with", "plus", "n"],
        "you": ["u", "ya", "your"],
        "love": ["adore", "heart", "cherish"],
        "miss": ["missing", "missed"],
        "sorry": ["apology", "forgive"],
        "happy": ["joy", "glad", "smile"],
        "sad": ["blue", "down", "crying"],
    }
    return alternatives.get(word.lower(), [f"'{word}' synonym", f"rhyme for '{word}'"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True, help="The message to encode in song titles")
    p.add_argument("--mode", default="word", choices=["word", "letter"])
    p.add_argument("--name", required=True, help="Playlist name")
    p.add_argument("--public", action="store_true")
    args = p.parse_args()

    sp = get_client()
    me = sp.me()
    print(f"Authenticated as {me['display_name']}", file=sys.stderr)

    track_ids = []
    results = []
    suggestions = []

    if args.mode == "word":
        words = args.text.strip().split()
        print(f"\nFinding songs for {len(words)} words...", file=sys.stderr)

        for word in words:
            tid, label, score = find_track_for_word(sp, word)
            if tid and score >= 0.8:
                track_ids.append(tid)
                results.append({"word": word, "track": label, "match": "exact" if score == 1.0 else "close"})
                print(f"  ✓ '{word}' → {label}", file=sys.stderr)
            elif tid and score >= 0.5:
                track_ids.append(tid)
                alts = suggest_word_alternatives(word)
                results.append({"word": word, "track": label, "match": "fuzzy", "alternatives": alts})
                suggestions.append(f"'{word}' matched loosely → consider: {', '.join(alts)}")
                print(f"  ~ '{word}' → {label} (fuzzy, score {score:.0%})", file=sys.stderr)
            else:
                alts = suggest_word_alternatives(word)
                results.append({"word": word, "track": None, "match": "none", "alternatives": alts})
                suggestions.append(f"'{word}' not found → try: {', '.join(alts)}")
                print(f"  ✗ '{word}' → NOT FOUND", file=sys.stderr)

    else:  # letter mode
        letters = [c for c in args.text.upper() if c.isalpha()]
        print(f"\nFinding songs for {len(letters)} letters: {' '.join(letters)}", file=sys.stderr)

        for letter in letters:
            tid, label = find_track_for_letter(sp, letter)
            if tid:
                track_ids.append(tid)
                results.append({"letter": letter, "track": label})
                print(f"  ✓ '{letter}' → {label}", file=sys.stderr)
            else:
                results.append({"letter": letter, "track": None})
                suggestions.append(f"No track found starting with '{letter}'")
                print(f"  ✗ '{letter}' → NOT FOUND", file=sys.stderr)

    if not track_ids:
        sys.exit("No tracks resolved.")

    pl = sp._post("me/playlists", payload={
        "name": args.name,
        "public": args.public,
        "description": f"Song titles spell: {args.text}",
    })
    sp.playlist_add_items(pl["id"], track_ids[:100])

    output = {
        "playlist_url": pl["external_urls"]["spotify"],
        "playlist_id": pl["id"],
        "message": args.text,
        "mode": args.mode,
        "tracks": results,
        "suggestions": suggestions,
    }

    if suggestions:
        output["note"] = "Some words didn't match perfectly. See 'suggestions' for text adjustments."

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
