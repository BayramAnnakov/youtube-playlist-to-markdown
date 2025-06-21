#!/usr/bin/env python3
"""
YouTube Playlist to Markdown Converter

This script downloads all videos from a YouTube playlist and converts them to markdown files.
It uses the existing transcribe_youtube_smart.py for robust transcription.
"""

import os
import sys
import argparse
import subprocess
import json
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from pathlib import Path
import time

def extract_playlist_id(url):
    """Extract playlist ID from YouTube playlist URL."""
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if 'list' in parse_qs(parsed_url.query):
            return parse_qs(parsed_url.query)['list'][0]
    
    # Try to extract from various URL patterns
    playlist_match = re.search(r'list=([A-Za-z0-9_-]+)', url)
    if playlist_match:
        return playlist_match.group(1)
    
    return None

def get_playlist_videos_ytdlp(playlist_url):
    """Get all video URLs from a playlist using yt-dlp."""
    try:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            playlist_url
        ]
        
        print("Fetching playlist information...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    video_id = video_data.get('id') or video_data.get('url')
                    if video_id:
                        # Ensure it's a full URL
                        if not video_id.startswith('http'):
                            video_id = f"https://www.youtube.com/watch?v={video_id}"
                        
                        videos.append({
                            'url': video_id,
                            'title': video_data.get('title', 'Unknown'),
                            'duration': video_data.get('duration', 0)
                        })
                except json.JSONDecodeError:
                    continue
        
        return videos
    except subprocess.CalledProcessError as e:
        print(f"Error fetching playlist: {e}")
        return []

def get_playlist_info(playlist_url):
    """Get playlist title and metadata."""
    try:
        cmd = [
            "yt-dlp",
            "--playlist-end", "1",
            "--dump-json",
            "--no-warnings",
            playlist_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout.strip().split('\n')[0])
        
        return {
            'title': data.get('playlist_title', 'Unknown Playlist'),
            'uploader': data.get('playlist_uploader', 'Unknown'),
            'count': data.get('playlist_count', 0)
        }
    except:
        return {
            'title': 'Unknown Playlist',
            'uploader': 'Unknown',
            'count': 0
        }

def sanitize_filename(filename):
    """Sanitize filename for filesystem compatibility."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    # Replace multiple spaces with single space
    filename = ' '.join(filename.split())
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()

def format_duration(seconds):
    """Format duration in seconds to human-readable format."""
    if not seconds:
        return "Unknown duration"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def transcribe_video(video_url, output_dir, mode="transcribe", force_method=None):
    """Transcribe a single video using transcribe_youtube_smart.py."""
    # Generate output filename based on video ID
    video_id = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', video_url)
    if video_id:
        output_file = os.path.join(output_dir, f"{video_id.group(1)}_{mode}.txt")
    else:
        output_file = os.path.join(output_dir, f"video_{int(time.time())}_{mode}.txt")
    
    cmd = [
        sys.executable,
        "transcribe_youtube_smart.py",
        video_url,
        "--mode", mode,
        "--output", output_file
    ]
    
    if force_method:
        if force_method == "gemini":
            cmd.append("--force-gemini")
        elif force_method == "ytdlp":
            cmd.append("--force-ytdlp")
    
    try:
        print(f"\nTranscribing: {video_url}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Try to extract output filename from stdout
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "saved to:" in line.lower() or "output:" in line.lower():
                    return True, line
            return True, "Transcription completed"
        else:
            return False, result.stderr or "Unknown error"
    except Exception as e:
        return False, str(e)

def create_playlist_summary(playlist_info, videos, output_dir, results):
    """Create a summary markdown file for the playlist."""
    summary_file = os.path.join(output_dir, "00_playlist_summary.md")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# {playlist_info['title']}\n\n")
        f.write(f"**Uploader:** {playlist_info['uploader']}\n")
        f.write(f"**Total Videos:** {len(videos)}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary statistics
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        f.write(f"## Processing Summary\n")
        f.write(f"- Successfully transcribed: {successful}\n")
        f.write(f"- Failed: {failed}\n\n")
        
        # Video list with status
        f.write("## Videos\n\n")
        for i, (video, result) in enumerate(zip(videos, results), 1):
            status = "✅" if result['success'] else "❌"
            f.write(f"{i}. {status} [{video['title']}]({video['url']}) - {format_duration(video['duration'])}\n")
            if not result['success']:
                f.write(f"   - Error: {result['error']}\n")
            else:
                f.write(f"   - Output: {result.get('output', 'Transcribed')}\n")
        
        # Failed videos section
        if failed > 0:
            f.write("\n## Failed Videos\n\n")
            for i, (video, result) in enumerate(zip(videos, results)):
                if not result['success']:
                    f.write(f"- [{video['title']}]({video['url']})\n")
                    f.write(f"  - Error: {result['error']}\n")
    
    print(f"\nPlaylist summary saved to: {summary_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert YouTube playlist videos to markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python youtube_playlist_to_markdown.py https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
  python youtube_playlist_to_markdown.py PLAYLIST_URL --output-dir my_playlist --mode summarize
  python youtube_playlist_to_markdown.py PLAYLIST_URL --start 5 --end 10 --delay 5"""
    )
    
    parser.add_argument('playlist_url', help='YouTube playlist URL')
    parser.add_argument('--output-dir', type=str, help='Output directory (auto-generated if not specified)')
    parser.add_argument('--mode', choices=['transcribe', 'summarize', 'outline'], 
                        default='transcribe', help='Processing mode (default: transcribe)')
    parser.add_argument('--force', choices=['api', 'gemini', 'ytdlp'],
                        help='Force a specific transcription method')
    parser.add_argument('--start', type=int, default=1, help='Start from video N (1-indexed)')
    parser.add_argument('--end', type=int, help='End at video N (inclusive)')
    parser.add_argument('--delay', type=int, default=2, 
                        help='Delay between videos in seconds (default: 2)')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip videos that already have output files')
    
    args = parser.parse_args()
    
    # Validate playlist URL
    playlist_id = extract_playlist_id(args.playlist_url)
    if not playlist_id:
        print("Error: Invalid YouTube playlist URL")
        sys.exit(1)
    
    # Get playlist information
    print(f"Processing playlist: {args.playlist_url}")
    playlist_info = get_playlist_info(args.playlist_url)
    print(f"Playlist: {playlist_info['title']} by {playlist_info['uploader']}")
    
    # Get all videos in playlist
    videos = get_playlist_videos_ytdlp(args.playlist_url)
    if not videos:
        print("Error: No videos found in playlist")
        sys.exit(1)
    
    print(f"Found {len(videos)} videos in playlist")
    
    # Apply start/end filters
    start_idx = max(0, args.start - 1)
    end_idx = min(len(videos), args.end) if args.end else len(videos)
    videos_to_process = videos[start_idx:end_idx]
    
    if start_idx > 0 or end_idx < len(videos):
        print(f"Processing videos {args.start} to {end_idx} (total: {len(videos_to_process)})")
    
    # Create output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Auto-generate directory name based on playlist title and date
        safe_title = sanitize_filename(playlist_info['title'])
        date_str = datetime.now().strftime("%Y%m%d")
        output_dir = f"{date_str}_{safe_title}_{args.mode}"
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Check if transcribe_youtube_smart.py exists
    if not os.path.exists("transcribe_youtube_smart.py"):
        print("Error: transcribe_youtube_smart.py not found in current directory")
        print("Please ensure the smart transcriber script is in the same directory")
        sys.exit(1)
    
    # Process each video
    results = []
    for i, video in enumerate(videos_to_process, 1):
        print(f"\n--- Processing video {i}/{len(videos_to_process)} ---")
        print(f"Title: {video['title']}")
        print(f"Duration: {format_duration(video['duration'])}")
        
        # Check if should skip existing
        if args.skip_existing:
            # Check if any transcript file exists for this video
            existing_files = list(Path(output_dir).glob(f"*{video['url'].split('=')[-1]}*.txt"))
            if existing_files:
                print(f"Skipping - output file already exists: {existing_files[0].name}")
                results.append({
                    'success': True,
                    'output': f"Skipped - already exists: {existing_files[0].name}"
                })
                continue
        
        # Transcribe the video
        success, message = transcribe_video(
            video['url'], 
            output_dir, 
            args.mode,
            args.force
        )
        
        results.append({
            'success': success,
            'output': message if success else None,
            'error': message if not success else None
        })
        
        if success:
            print(f"✅ Success: {message}")
        else:
            print(f"❌ Failed: {message}")
        
        # Delay between videos (except for the last one)
        if i < len(videos_to_process) and args.delay > 0:
            print(f"Waiting {args.delay} seconds before next video...")
            time.sleep(args.delay)
    
    # Create summary file
    create_playlist_summary(playlist_info, videos_to_process, output_dir, results)
    
    # Final summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n{'='*50}")
    print(f"Playlist processing complete!")
    print(f"Successfully processed: {successful}/{len(videos_to_process)} videos")
    print(f"Output directory: {output_dir}")
    
    if successful < len(videos_to_process):
        print(f"\n⚠️  {len(videos_to_process) - successful} videos failed to process.")
        print("Check the playlist summary for details.")

if __name__ == "__main__":
    main()