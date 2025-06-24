#!/usr/bin/env python3
"""
Smart YouTube transcriber that tries multiple methods:
1. YouTube Transcript API (fastest, no token limits)
2. Gemini API (for videos without transcripts)
3. Handles various edge cases automatically
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import argparse
import subprocess
from urllib.parse import urlparse, parse_qs
import re
import json
from datetime import datetime
from pathlib import Path

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname in ['youtu.be', 'www.youtu.be']:
        return parsed_url.path[1:]
    
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    
    return None

def check_youtube_transcript_api():
    """Check if youtube-transcript-api is installed."""
    try:
        import youtube_transcript_api
        return True
    except ImportError:
        return False

def install_youtube_transcript_api():
    """Install youtube-transcript-api package."""
    print("Installing youtube-transcript-api...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "youtube-transcript-api"])
        print("Successfully installed youtube-transcript-api")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install youtube-transcript-api")
        return False

def get_video_title(url):
    """Get video title using yt-dlp."""
    try:
        cmd = [
            "yt-dlp", 
            "--get-title", 
            "--no-warnings",
            "--extractor-args", "youtube:player_client=android",
            "--user-agent", "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        # Fallback: try to get from youtube-dl or return None
        try:
            cmd = ["youtube-dl", "--get-title", "--no-warnings", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return None

def sanitize_filename(filename):
    """Sanitize filename for filesystem compatibility."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    # Replace multiple spaces with single space
    filename = ' '.join(filename.split())
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()

def generate_output_filename(url, mode="transcribe"):
    """Generate output filename based on video title and current date."""
    # Get current date
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Try to get video title
    title = get_video_title(url)
    if title:
        # Sanitize title for filename
        safe_title = sanitize_filename(title)
        # Create filename
        filename = f"{date_str}_{safe_title}_{mode}.txt"
    else:
        # Fallback to video ID
        video_id = extract_video_id(url)
        filename = f"{date_str}_youtube_{video_id}_{mode}.txt"
    
    return filename

def try_youtube_api(url, output_file=None):
    """Try to get transcript using YouTube Transcript API."""
    print("Attempting to fetch transcript using YouTube API...")
    
    # Get the path to transcribe_youtube_api.py in the same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_script = os.path.join(script_dir, "transcribe_youtube_api.py")
    
    cmd = [sys.executable, api_script, url]
    if output_file:
        cmd.extend(["-o", output_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not output_file:
                print(result.stdout)
            return True
        else:
            # Check if it's a "no transcript" error
            error_text = result.stdout + " " + result.stderr
            if "No transcripts" in error_text or "doesn't have any transcripts" in error_text:
                print("No transcripts available via YouTube API")
                return False
            else:
                print(f"YouTube API error: {result.stdout}\n{result.stderr}")
                return False
    except FileNotFoundError:
        print("transcribe_youtube_api.py not found")
        return False

def try_gemini_api(url, output_file=None, mode="transcribe"):
    """Try to get transcript using Gemini API."""
    print(f"Attempting to {mode} using Gemini API...")
    
    # Get the path to transcribe_youtube.py in the same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gemini_script = os.path.join(script_dir, "transcribe_youtube.py")
    
    cmd = [sys.executable, gemini_script, url, "--mode", mode]
    if output_file:
        cmd.extend(["-o", output_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not output_file:
                print(result.stdout)
            return True
        else:
            # Check for token limit error
            if "exceeds token limit" in result.stdout or "exceeds the maximum number of tokens" in result.stderr:
                print("Video too long for Gemini API")
                return "token_limit"
            else:
                print(f"Gemini API error: {result.stdout}")
                return False
    except FileNotFoundError:
        print("transcribe_youtube.py not found")
        return False

def try_ytdlp_gemini(url, output_file=None, mode="transcribe"):
    """Try to transcribe by downloading audio with yt-dlp and using Gemini."""
    print(f"Attempting to {mode} using yt-dlp + Gemini...")
    
    # Get the path to transcribe_youtube_ytdlp.py in the same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ytdlp_script = os.path.join(script_dir, "transcribe_youtube_ytdlp.py")
    
    cmd = [sys.executable, ytdlp_script, url, "--mode", mode]
    if output_file:
        cmd.extend(["-o", output_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not output_file:
                print(result.stdout)
            return True
        else:
            print(f"yt-dlp + Gemini error:")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return False
    except FileNotFoundError:
        print("transcribe_youtube_ytdlp.py not found")
        return False

def main():
    parser = argparse.ArgumentParser(description="Smart YouTube transcriber with automatic fallback")
    parser.add_argument("url", help="YouTube video URL to transcribe")
    parser.add_argument("--output", "-o", help="Output file path (defaults to auto-generated name)")
    parser.add_argument("--no-auto-output", action="store_true",
                        help="Don't automatically save to file, print to stdout instead")
    parser.add_argument("--force-gemini", action="store_true", 
                        help="Skip YouTube API and use Gemini directly")
    parser.add_argument("--force-ytdlp", action="store_true",
                        help="Skip other methods and use yt-dlp + Gemini directly")
    parser.add_argument("--mode", choices=["transcribe", "summarize", "outline"], default="transcribe",
                        help="Gemini processing mode if YouTube API fails")
    
    args = parser.parse_args()
    
    # Validate URL
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Invalid YouTube URL: {args.url}")
        return 1
    
    print(f"Processing video: {args.url}")
    print(f"Video ID: {video_id}")
    
    # Generate output filename if not provided and not disabled
    if not args.output and not args.no_auto_output:
        args.output = generate_output_filename(args.url, args.mode)
        print(f"Output file: {args.output}")
    
    print()  # Empty line for readability
    
    success = False
    
    # Step 1: If forced to use yt-dlp, skip other methods
    if args.force_ytdlp:
        success = try_ytdlp_gemini(args.url, args.output, args.mode)
    
    # Step 2: Try YouTube Transcript API (unless forced to use Gemini)
    elif not args.force_gemini:
        # Check if youtube-transcript-api is installed
        if not check_youtube_transcript_api():
            print("youtube-transcript-api not installed.")
            response = input("Would you like to install it? (y/n): ")
            if response.lower() == 'y':
                if not install_youtube_transcript_api():
                    print("Continuing without YouTube API...")
            else:
                print("Continuing without YouTube API...")
        
        if check_youtube_transcript_api():
            success = try_youtube_api(args.url, args.output)
    
    # Step 3: If YouTube API failed, try Gemini direct
    if not success and not args.force_ytdlp:
        result = try_gemini_api(args.url, args.output, args.mode)
        
        # Step 4: If token limit exceeded, try yt-dlp + Gemini
        if result == "token_limit":
            print("\nVideo too long for direct processing. Trying yt-dlp audio download...")
            success = try_ytdlp_gemini(args.url, args.output, args.mode)
            
            # Step 5: If still failing, try summary/outline modes
            if not success and args.mode == "transcribe":
                print("\nTrying summary mode...")
                success = try_ytdlp_gemini(args.url, args.output, "summarize")
                
                if not success:
                    print("\nTrying outline mode...")
                    success = try_ytdlp_gemini(args.url, args.output, "outline")
        else:
            success = result == True
    
    if success:
        if args.output:
            print(f"\nSuccessfully saved to: {args.output}")
        return 0
    else:
        print("\nFailed to transcribe video using all available methods.")
        print("\nPossible solutions:")
        print("1. For long videos, try downloading and processing in chunks")
        print("2. Check if the video is private or age-restricted")
        print("3. Verify your API keys are set correctly")
        return 1

if __name__ == "__main__":
    exit(main())