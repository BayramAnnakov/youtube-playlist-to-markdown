from youtube_transcript_api import YouTubeTranscriptApi
import argparse
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from pathlib import Path
import subprocess

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # Handle different YouTube URL formats
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            # Standard format: https://www.youtube.com/watch?v=VIDEO_ID
            return parse_qs(parsed_url.query).get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            # Embed format: https://www.youtube.com/embed/VIDEO_ID
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname in ['youtu.be', 'www.youtu.be']:
        # Short format: https://youtu.be/VIDEO_ID
        return parsed_url.path[1:]
    
    # Try to extract video ID using regex as fallback
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

def get_transcript(video_id, languages=None):
    """Get transcript for a YouTube video."""
    try:
        if languages:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(languages)
            return transcript.fetch()
        else:
            # Get transcript in any available language
            return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        raise Exception(f"Failed to get transcript: {str(e)}")

def format_transcript(transcript_data, format_type="text", include_timestamps=False):
    """Format transcript data."""
    if format_type == "json":
        import json
        return json.dumps(transcript_data, indent=2)
    else:
        if include_timestamps:
            # Custom formatting with timestamps
            lines = []
            for entry in transcript_data:
                timestamp = f"[{int(entry['start']//60):02d}:{int(entry['start']%60):02d}]"
                text = entry['text'].strip()
                lines.append(f"{timestamp} {text}")
            return "\n".join(lines)
        else:
            # Plain text without timestamps
            lines = []
            for entry in transcript_data:
                text = entry['text'].strip()
                if text:
                    lines.append(text)
            return " ".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos using YouTube Transcript API")
    parser.add_argument("url", help="YouTube video URL to transcribe")
    parser.add_argument("--languages", "-l", nargs="+", help="Preferred languages (e.g., en es fr)")
    parser.add_argument("--format", choices=["text", "json"], default="text", 
                        help="Output format (default: text)")
    parser.add_argument("--timestamps", "-t", action="store_true", 
                        help="Include timestamps in text format")
    parser.add_argument("--output", "-o", help="Output file path (defaults to auto-generated name)")
    parser.add_argument("--no-auto-output", action="store_true",
                        help="Don't automatically save to file, print to stdout instead")
    parser.add_argument("--list-languages", action="store_true", 
                        help="List available languages for this video")
    
    args = parser.parse_args()
    
    # Extract video ID from URL
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {args.url}")
        return 1
    
    print(f"Video ID: {video_id}")
    
    # Generate output filename if not provided and not disabled
    if not args.output and not args.no_auto_output:
        args.output = generate_output_filename(args.url, "transcribe")
        print(f"Output file: {args.output}")
    
    try:
        if args.list_languages:
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print("\nAvailable transcripts:")
            for transcript in transcript_list:
                lang_info = f"{transcript.language} ({transcript.language_code})"
                if transcript.is_generated:
                    lang_info += " [Auto-generated]"
                if transcript.is_translatable:
                    lang_info += " [Translatable]"
                print(f"  - {lang_info}")
            return 0
        
        # Get transcript
        print("Fetching transcript...")
        transcript_data = get_transcript(video_id, args.languages)
        
        # Format transcript
        formatted_transcript = format_transcript(
            transcript_data, 
            format_type=args.format,
            include_timestamps=args.timestamps
        )
        
        # Output result
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)
            print(f"\nTranscript saved to: {args.output}")
        else:
            print("\n--- TRANSCRIPT ---\n")
            print(formatted_transcript)
            
    except Exception as e:
        print(f"Error: {e}")
        
        # Provide helpful suggestions
        if "No transcripts" in str(e):
            print("\nThis video doesn't have any transcripts available.")
            print("Possible reasons:")
            print("- The video owner disabled captions")
            print("- The video is too new (captions not yet generated)")
            print("- The video is private or age-restricted")
            print("\nTry using the Gemini-based transcriber for videos without captions:")
            print(f"  python transcribe_youtube.py {args.url}")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())