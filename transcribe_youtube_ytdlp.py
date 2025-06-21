#!/usr/bin/env python3
"""
YouTube transcriber using yt-dlp to download audio and Gemini to transcribe.
This method works for long videos by processing audio files instead of video URLs.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import subprocess
import tempfile
import argparse
from pathlib import Path
import json
import time
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs

from google import genai

GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
}

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

def get_video_title(url):
    """Get video title using yt-dlp."""
    try:
        cmd = ["yt-dlp", "--get-title", "--no-warnings", url]
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

def check_ytdlp():
    """Check if yt-dlp is installed."""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_ytdlp():
    """Install yt-dlp."""
    print("Installing yt-dlp...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        print("Successfully installed yt-dlp")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install yt-dlp via pip. Try: brew install yt-dlp (macOS) or sudo apt install yt-dlp (Linux)")
        return False

def get_video_info(url):
    """Get video information using yt-dlp."""
    try:
        cmd = [
            "yt-dlp", 
            "--dump-json", 
            "--no-warnings",
            "--extractor-args", "youtube:player_client=android",
            "--user-agent", "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "upload_date": info.get("upload_date", "Unknown"),
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def download_audio(url, output_path):
    """Download audio from YouTube video using yt-dlp."""
    print("Downloading audio...")
    try:
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
            "-o", str(output_path),
            "--no-warnings",
            "--quiet",
            "--progress",
            "--extractor-args", "youtube:player_client=android",  # Use Android client to avoid bot detection
            "--user-agent", "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
            url
        ]
        subprocess.run(cmd, check=True)
        
        # yt-dlp adds extension, so check for the actual file
        mp3_path = Path(str(output_path) + ".mp3")
        if mp3_path.exists():
            return mp3_path
        
        # Check if file exists without extension
        if Path(output_path).exists():
            return Path(output_path)
            
        # Look for any audio file in the temp directory
        parent_dir = Path(output_path).parent
        audio_files = list(parent_dir.glob(f"{Path(output_path).stem}.*"))
        if audio_files:
            return audio_files[0]
            
        raise FileNotFoundError("Audio file not found after download")
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to download audio: {e}")

def upload_to_gemini(file_path):
    """Upload file to Gemini for processing."""
    print("Uploading audio to Gemini...")
    
    try:
        import google.generativeai as genai_old
        
        # Configure the API
        genai_old.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Determine MIME type based on file extension
        file_ext = Path(file_path).suffix.lower()
        mime_type_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }
        
        mime_type = mime_type_map.get(file_ext, 'audio/mpeg')  # Default to mp3
        print(f"Using MIME type: {mime_type}")
        
        # Upload the file
        uploaded_file = genai_old.upload_file(str(file_path), mime_type=mime_type)
        
        # Wait for file to be processed
        print("Waiting for file processing...")
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai_old.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            raise Exception("File upload failed")
            
        return uploaded_file
    except Exception as e:
        raise Exception(f"Failed to upload file: {e}")

def transcribe_audio_with_gemini(uploaded_file, model="pro", mode="transcribe"):
    """Transcribe uploaded audio file using Gemini."""
    print(f"Transcribing audio ({mode} mode)...")
    
    try:
        import google.generativeai as genai_old
        
        if mode == "transcribe":
            prompt = "Please provide a detailed transcription of this audio file. Include all spoken content with proper punctuation and paragraph breaks."
        elif mode == "summarize":
            prompt = "Please provide a comprehensive summary of this audio file, including key points, main topics discussed, and important takeaways."
        elif mode == "outline":
            prompt = "Please provide a detailed outline of this audio file with timestamps, main sections, key points discussed in each section, and important quotes or insights."
        
        # Map model names to full model names
        model_mapping = {
            "flash": "gemini-2.5-flash",
            "pro": "gemini-2.5-pro"
        }
        
        model_name = model_mapping.get(model, "gemini-2.5-pro")
        genai_model = genai_old.GenerativeModel(model_name)
        
        response = genai_model.generate_content([prompt, uploaded_file])
        
        return response.text
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {e}")

def cleanup_gemini_file(uploaded_file):
    """Delete uploaded file from Gemini."""
    try:
        import google.generativeai as genai_old
        genai_old.delete_file(uploaded_file.name)
        print("Cleaned up uploaded file")
    except Exception as e:
        print(f"Warning: Failed to cleanup uploaded file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos by downloading audio with yt-dlp")
    parser.add_argument("url", help="YouTube video URL to transcribe")
    parser.add_argument("--model", choices=["flash", "pro"], default="pro", 
                        help="Gemini model to use (default: pro)")
    parser.add_argument("--mode", choices=["transcribe", "summarize", "outline"], default="transcribe",
                        help="Processing mode (default: transcribe)")
    parser.add_argument("--output", "-o", help="Output file path (defaults to auto-generated name)")
    parser.add_argument("--no-auto-output", action="store_true",
                        help="Don't automatically save to file, print to stdout instead")
    parser.add_argument("--keep-audio", action="store_true", 
                        help="Keep downloaded audio file")
    parser.add_argument("--audio-output", help="Path to save audio file (implies --keep-audio)")
    
    args = parser.parse_args()
    
    # Check if yt-dlp is installed
    if not check_ytdlp():
        print("yt-dlp is not installed.")
        response = input("Would you like to install it? (y/n): ")
        if response.lower() == 'y':
            if not install_ytdlp():
                return 1
        else:
            print("yt-dlp is required for this script.")
            return 1
    
    # Get video info
    print(f"Getting video information...")
    video_info = get_video_info(args.url)
    if video_info:
        print(f"Title: {video_info['title']}")
        duration_min = video_info['duration'] // 60
        duration_sec = video_info['duration'] % 60
        print(f"Duration: {duration_min}:{duration_sec:02d}")
        print(f"Uploader: {video_info['uploader']}")
    
    # Generate output filename if not provided and not disabled
    if not args.output and not args.no_auto_output:
        args.output = generate_output_filename(args.url, args.mode)
        print(f"Output file: {args.output}")
    
    uploaded_file = None
    audio_path = None
    
    try:
        # Create temporary directory for audio
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download audio
            if args.audio_output:
                audio_path = Path(args.audio_output)
                args.keep_audio = True
            else:
                audio_path = Path(temp_dir) / "audio"
            
            downloaded_path = download_audio(args.url, audio_path)
            print(f"Audio downloaded: {downloaded_path}")
            
            # Check file size
            file_size_mb = downloaded_path.stat().st_size / (1024 * 1024)
            print(f"Audio file size: {file_size_mb:.1f} MB")
            
            # Upload to Gemini
            uploaded_file = upload_to_gemini(downloaded_path)
            
            # Transcribe
            result = transcribe_audio_with_gemini(uploaded_file, args.model, args.mode)
            
            # Save or print result
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"\nTranscription saved to: {args.output}")
            else:
                print(f"\n--- {args.mode.upper()} ---\n")
                print(result)
            
            # Copy audio file if requested
            if args.keep_audio and not args.audio_output:
                import shutil
                output_audio = Path(f"{Path(args.output).stem if args.output else 'audio'}.mp3")
                shutil.copy2(downloaded_path, output_audio)
                print(f"Audio saved to: {output_audio}")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        # Cleanup Gemini file
        if uploaded_file:
            cleanup_gemini_file(uploaded_file)
    
    return 0

if __name__ == "__main__":
    exit(main())