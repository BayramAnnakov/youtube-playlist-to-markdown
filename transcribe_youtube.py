from dotenv import load_dotenv
load_dotenv()

from google import genai
import os
import argparse
import time
import random
from datetime import datetime
from pathlib import Path
import subprocess
import re
from urllib.parse import urlparse, parse_qs

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

def transcribe_youtube_video(youtube_url, model="pro", max_retries=5, mode="transcribe"):
    """Transcribe a YouTube video using Google Gemini API with retry logic."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    if mode == "transcribe":
        prompt = "Please provide a detailed transcription of this YouTube video. Include all spoken content, and note any significant visual elements or context when relevant."
    elif mode == "summarize":
        prompt = "Please provide a comprehensive summary of this YouTube video, including key points, main topics discussed, and important takeaways. Try to capture as much detail as possible."
    elif mode == "outline":
        prompt = "Please provide a detailed outline of this YouTube video with timestamps (if visible), main sections, key points discussed in each section, and important quotes or insights."
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODELS[model],
                contents=[
                    {
                        "parts": [
                            {"text": prompt},
                            {"file_data": {"file_uri": youtube_url}},
                        ]
                    }
                ],
            )
            
            return response.text
            
        except Exception as e:
            error_str = str(e)
            if "503" in error_str and "overloaded" in error_str.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"\nModel overloaded. Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Model overloaded after {max_retries} attempts. Please try again later.")
            elif "exceeds the maximum number of tokens" in error_str:
                # Token limit exceeded - can't process this video
                raise Exception(f"Video is too long to process (exceeds token limit). Consider using a YouTube transcript API or downloading and processing the video in chunks.")
            else:
                # Re-raise other errors immediately
                raise

def main():
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos using Google Gemini")
    parser.add_argument("url", help="YouTube video URL to transcribe")
    parser.add_argument("--model", choices=["flash", "pro"], default="pro", 
                        help="Gemini model to use (default: pro)")
    parser.add_argument("--mode", choices=["transcribe", "summarize", "outline"], default="transcribe",
                        help="Processing mode: transcribe (full transcript), summarize (summary), or outline (structured outline)")
    parser.add_argument("--output", "-o", help="Output file path (defaults to auto-generated name)")
    parser.add_argument("--no-auto-output", action="store_true",
                        help="Don't automatically save to file, print to stdout instead")
    
    args = parser.parse_args()
    
    print(f"Processing video: {args.url}")
    print(f"Using model: {GEMINI_MODELS[args.model]}")
    print(f"Mode: {args.mode}")
    
    # Generate output filename if not provided and not disabled
    if not args.output and not args.no_auto_output:
        args.output = generate_output_filename(args.url, args.mode)
        print(f"Output file: {args.output}")
    
    try:
        result = transcribe_youtube_video(args.url, args.model, mode=args.mode)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\nOutput saved to: {args.output}")
        else:
            print(f"\n--- {args.mode.upper()} ---\n")
            print(result)
            
    except Exception as e:
        print(f"Error processing video: {e}")
        
        # If it's a token limit error, suggest alternatives
        if "exceeds token limit" in str(e):
            print("\nAlternative approaches for long videos:")
            print("1. Use --mode summarize or --mode outline for a condensed version")
            print("2. Use youtube-transcript-api to get text transcripts directly")
            print("3. Download the video and process it in segments")
            print("4. Use YouTube's auto-generated captions if available")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())