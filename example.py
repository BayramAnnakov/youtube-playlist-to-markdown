#!/usr/bin/env python3
"""
Example usage of YouTube Playlist to Markdown tool

This script demonstrates various ways to use the tool.
"""

import subprocess
import sys

def run_example(description, command):
    """Run an example command and print description."""
    print(f"\n{'='*60}")
    print(f"Example: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)
    
    # Uncomment the next line to actually run the commands
    # subprocess.run(command)
    print("(Command displayed but not executed - uncomment line in script to run)")

def main():
    """Run various example commands."""
    print("YouTube Playlist to Markdown - Example Usage")
    print("============================================")
    
    # Example playlist URL (you'll need to replace with a real one)
    playlist_url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    
    # Basic usage
    run_example(
        "Basic playlist processing",
        [sys.executable, "youtube_playlist_to_markdown.py", playlist_url]
    )
    
    # Summary mode
    run_example(
        "Create summaries instead of full transcripts",
        [sys.executable, "youtube_playlist_to_markdown.py", playlist_url, "--mode", "summarize"]
    )
    
    # Process specific range
    run_example(
        "Process only videos 1-5 from the playlist",
        [sys.executable, "youtube_playlist_to_markdown.py", playlist_url, "--start", "1", "--end", "5"]
    )
    
    # Skip existing files
    run_example(
        "Resume processing - skip already completed videos",
        [sys.executable, "youtube_playlist_to_markdown.py", playlist_url, "--skip-existing"]
    )
    
    # Custom output directory
    run_example(
        "Save to custom directory",
        [sys.executable, "youtube_playlist_to_markdown.py", playlist_url, "--output-dir", "my_transcripts"]
    )
    
    # Convert to enhanced markdown
    run_example(
        "Enhance transcripts with metadata",
        [sys.executable, "convert_transcripts_to_markdown.py", "my_transcripts/"]
    )
    
    # Single video transcription
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    run_example(
        "Transcribe a single video",
        [sys.executable, "transcribe_youtube_smart.py", video_url]
    )
    
    print("\n" + "="*60)
    print("Note: Replace the playlist URL with your own playlist!")
    print("Make sure to set your GEMINI_API_KEY in the .env file")
    print("="*60)

if __name__ == "__main__":
    main()