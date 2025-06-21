# YouTube Playlist to Markdown

A powerful Python tool that converts entire YouTube playlists into well-formatted markdown files. Perfect for creating transcripts, documentation, research notes, or archiving video content in a readable format.

## Features

- 📋 **Batch Processing**: Process entire YouTube playlists with a single command
- 🚀 **Smart Transcription**: Multiple transcription methods with automatic fallback
- 📝 **Rich Metadata**: Includes video title, channel, duration, views, and more
- 🔄 **Resume Support**: Skip already processed videos to save time
- 🎯 **Flexible Output**: Choose between transcription, summary, or outline modes
- 💾 **Clean Markdown**: Well-formatted output with proper headings and metadata

## Transcription Methods

The tool uses a smart multi-method approach:

1. **YouTube Transcript API** (fastest, no API limits)
   - Fetches existing captions/subtitles
   - No token consumption
   - Works when captions are available

2. **Google Gemini API** (direct video processing)
   - Processes videos without captions
   - High-quality transcription
   - May have token limits for long videos

3. **Audio Download + Gemini** (for long videos)
   - Downloads audio first
   - Processes in chunks
   - Handles videos that exceed API limits

## Prerequisites

- Python 3.7+
- `yt-dlp` or `youtube-dl` command-line tool
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-playlist-to-markdown.git
cd youtube-playlist-to-markdown
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install yt-dlp (recommended) or youtube-dl:
```bash
# Using pip
pip install yt-dlp

# Or using homebrew (macOS)
brew install yt-dlp

# Or download directly
# https://github.com/yt-dlp/yt-dlp#installation
```

4. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

## Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## Usage

### Basic Usage

Process an entire YouTube playlist:
```bash
python youtube_playlist_to_markdown.py https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID
```

### Advanced Options

```bash
# Process as summaries instead of full transcripts
python youtube_playlist_to_markdown.py PLAYLIST_URL --mode summarize

# Process only videos 5-10 from the playlist
python youtube_playlist_to_markdown.py PLAYLIST_URL --start 5 --end 10

# Skip videos that already have output files
python youtube_playlist_to_markdown.py PLAYLIST_URL --skip-existing

# Custom output directory
python youtube_playlist_to_markdown.py PLAYLIST_URL --output-dir my_transcripts

# Add delay between videos (in seconds)
python youtube_playlist_to_markdown.py PLAYLIST_URL --delay 5

# Force a specific transcription method
python youtube_playlist_to_markdown.py PLAYLIST_URL --force api  # or gemini, ytdlp
```

### Convert Transcripts to Enhanced Markdown

After processing, you can enhance the transcripts with metadata:
```bash
python convert_transcripts_to_markdown.py transcript_folder/
```

This adds:
- Video metadata (views, likes, upload date)
- Proper formatting and structure
- Clickable video links
- Channel information

## Output Structure

The tool creates organized output:
```
20250621_PlaylistName_transcribe/
├── 00_playlist_summary.md      # Overview of all videos
├── VideoID1_transcribe.txt     # Raw transcript
├── VideoID2_transcribe.txt
└── ...

20250621_PlaylistName_transcribe_markdown/
├── VideoID1_transcribe.md      # Enhanced markdown
├── VideoID2_transcribe.md
└── ...
```

## Example Output

Each markdown file includes:

```markdown
# Video Title

## Video Information
- **URL**: [https://youtube.com/watch?v=...](...)
- **Channel**: Channel Name
- **Published**: January 1, 2024
- **Duration**: 15m 30s
- **Views**: 1,234,567
- **Likes**: 12,345

## Description
Video description here...

## Transcript
Full transcript or summary content...
```

## Processing Modes

- **transcribe**: Full word-for-word transcript
- **summarize**: Concise summary of key points
- **outline**: Structured outline of main topics

## Troubleshooting

### "The playlist does not exist"
- Ensure the playlist is public
- Check the playlist URL is correct
- Try using the playlist ID directly

### API Key Issues
- Verify your Gemini API key is correct
- Check you have API access enabled
- Ensure you haven't exceeded quota limits

### Missing Transcripts
- Some videos may not have captions available
- The tool will automatically try alternative methods
- Check the playlist summary for any failed videos

### Installation Issues
- Make sure you have Python 3.7 or newer
- Try upgrading pip: `python -m pip install --upgrade pip`
- On macOS/Linux, you might need to use `python3` instead of `python`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Uses the excellent [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) library
- Powered by Google's Gemini AI for transcription
- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video information

## Disclaimer

This tool is for educational and personal use. Please respect copyright laws and YouTube's Terms of Service when using this tool. Always ensure you have the right to transcribe and store content from YouTube videos.