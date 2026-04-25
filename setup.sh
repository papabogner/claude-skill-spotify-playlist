#!/bin/bash
# spotify-playlist skill setup helper

set -e

echo "=== Spotify Playlist Skill Setup ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Install from https://python.org"
    exit 1
fi

# Install spotipy
echo "Installing spotipy..."
pip install spotipy -q && echo "✓ spotipy installed"

# Optional yt-dlp
read -p "Install yt-dlp for YouTube URL support? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install yt-dlp -q && echo "✓ yt-dlp installed"
fi

# Create config dir
mkdir -p ~/.config/spotify-skill
chmod 700 ~/.config/spotify-skill

# Credentials
if [ -f ~/.config/spotify-skill/credentials.json ]; then
    echo ""
    echo "✓ Credentials already exist at ~/.config/spotify-skill/credentials.json"
else
    echo ""
    echo "Open https://developer.spotify.com/dashboard and create an app."
    echo "Set Redirect URI to: http://127.0.0.1:8888/callback"
    echo ""
    read -p "Client ID: " CLIENT_ID
    read -p "Client Secret: " CLIENT_SECRET

    cat > ~/.config/spotify-skill/credentials.json << EOF
{
  "client_id": "$CLIENT_ID",
  "client_secret": "$CLIENT_SECRET",
  "redirect_uri": "http://127.0.0.1:8888/callback"
}
EOF
    chmod 600 ~/.config/spotify-skill/credentials.json
    echo "✓ Credentials saved"
fi

echo ""
echo "=== Setup complete ==="
echo "In Claude Code: 'create a playlist called X with these tracks: ...'"
