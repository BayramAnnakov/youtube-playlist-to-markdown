# Quick Start Guide

Get up and running in 5 minutes!

## 1. Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-playlist-to-markdown.git
cd youtube-playlist-to-markdown

# Run the setup script
python setup.py
```

## 2. Get Your API Key (2 minutes)

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key

## 3. Configure API Key (30 seconds)

Edit the `.env` file:
```bash
GEMINI_API_KEY=paste_your_key_here
```

## 4. Run Your First Transcription (30 seconds)

```bash
# Transcribe a playlist
python youtube_playlist_to_markdown.py https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID

# Or transcribe a single video
python transcribe_youtube_smart.py https://www.youtube.com/watch?v=VIDEO_ID
```

## That's it! 🎉

Your transcripts will be saved in a timestamped folder.

## Common Issues

**"yt-dlp not found"**
```bash
pip install yt-dlp
```

**"Playlist does not exist"**
- Make sure the playlist is public
- Use the full playlist URL

**API errors**
- Check your API key is correct
- Verify you have API access enabled

## Next Steps

- Run `python example.py` to see more usage examples
- Check the [README](README.md) for advanced options
- Process multiple playlists with different modes