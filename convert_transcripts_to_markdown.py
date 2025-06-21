#!/usr/bin/env python3
"""
Convert YouTube transcript text files to well-formatted markdown files.

This script takes the output from youtube_playlist_to_markdown.py and converts
the raw text transcripts into properly formatted markdown with:
- Video metadata
- Proper headings
- Timestamps (if available)
- Clean formatting
"""

import os
import re
import argparse
from pathlib import Path
from datetime import datetime
import json
import subprocess

def extract_video_id_from_filename(filename):
    """Extract YouTube video ID from filename."""
    # Common patterns in filenames
    patterns = [
        r'^([A-Za-z0-9_-]{11})_',       # ID at start followed by _
        r'([A-Za-z0-9_-]{11})\.txt$',  # Just the ID before .txt
        r'youtube_([A-Za-z0-9_-]{11})',  # youtube_ID
        r'v=([A-Za-z0-9_-]{11})',       # URL parameter
        r'_([A-Za-z0-9_-]{11})_',       # ID in middle
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    return None

def get_video_metadata(video_id):
    """Get video metadata using yt-dlp."""
    if not video_id:
        return {}
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        return {
            'title': data.get('title', 'Unknown Title'),
            'uploader': data.get('uploader', 'Unknown Channel'),
            'upload_date': data.get('upload_date', ''),
            'duration': data.get('duration', 0),
            'view_count': data.get('view_count', 0),
            'like_count': data.get('like_count', 0),
            'description': data.get('description', ''),
            'url': url
        }
    except:
        return {}

def format_number(num):
    """Format large numbers with commas."""
    if not num:
        return "0"
    return f"{num:,}"

def format_date(date_str):
    """Format date from YYYYMMDD to readable format."""
    if not date_str or len(date_str) != 8:
        return "Unknown date"
    
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str

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

def clean_transcript_text(text):
    """Clean and format transcript text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Fix common transcript issues
    text = text.replace(' ,', ',')
    text = text.replace(' .', '.')
    text = text.replace(' ?', '?')
    text = text.replace(' !', '!')
    
    # Add proper paragraph breaks (assuming sentences ending with . ? ! followed by capital letter)
    text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', text)
    
    return text.strip()

def detect_transcript_type(content):
    """Detect if the transcript has timestamps or is plain text."""
    # Check for common timestamp patterns
    timestamp_patterns = [
        r'\[\d+:\d+\]',           # [00:30]
        r'\d+:\d+:\d+',           # 00:30:45
        r'^\d+:\d+\s',            # 00:30 at line start
        r'\{\d+\}',               # {30} seconds
    ]
    
    for pattern in timestamp_patterns:
        if re.search(pattern, content, re.MULTILINE):
            return 'timestamped'
    
    # Check if it's a summary or outline
    if any(keyword in content.lower()[:200] for keyword in ['summary:', 'outline:', 'key points:', 'overview:']):
        return 'summary'
    
    return 'plain'

def format_timestamped_transcript(content):
    """Format transcript with timestamps into markdown."""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to detect and format timestamps
        timestamp_match = re.match(r'^(\[?\d+:\d+(?::\d+)?\]?)\s*(.+)', line)
        if timestamp_match:
            timestamp, text = timestamp_match.groups()
            # Clean up timestamp
            timestamp = timestamp.strip('[]')
            formatted_lines.append(f"**{timestamp}** - {text}")
        else:
            formatted_lines.append(line)
    
    return '\n\n'.join(formatted_lines)

def convert_to_markdown(txt_file, output_dir, fetch_metadata=True):
    """Convert a transcript text file to markdown."""
    print(f"\nProcessing: {txt_file.name}")
    
    # Read the content
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False
    
    # Get video metadata if possible
    metadata = {}
    if fetch_metadata:
        video_id = extract_video_id_from_filename(txt_file.name)
        if video_id:
            print(f"  Fetching metadata for video ID: {video_id}")
            metadata = get_video_metadata(video_id)
    
    # Detect transcript type
    transcript_type = detect_transcript_type(content)
    print(f"  Detected type: {transcript_type}")
    
    # Create markdown content
    md_lines = []
    
    # Title
    title = metadata.get('title', txt_file.stem)
    md_lines.append(f"# {title}\n")
    
    # Metadata section
    if metadata:
        md_lines.append("## Video Information\n")
        if metadata.get('url'):
            md_lines.append(f"- **URL**: [{metadata['url']}]({metadata['url']})")
        if metadata.get('uploader'):
            md_lines.append(f"- **Channel**: {metadata['uploader']}")
        if metadata.get('upload_date'):
            md_lines.append(f"- **Published**: {format_date(metadata['upload_date'])}")
        if metadata.get('duration'):
            md_lines.append(f"- **Duration**: {format_duration(metadata['duration'])}")
        if metadata.get('view_count'):
            md_lines.append(f"- **Views**: {format_number(metadata['view_count'])}")
        if metadata.get('like_count'):
            md_lines.append(f"- **Likes**: {format_number(metadata['like_count'])}")
        md_lines.append("")  # Empty line
    
    # Add description if available
    if metadata.get('description'):
        md_lines.append("## Description\n")
        # Truncate very long descriptions
        desc = metadata['description']
        if len(desc) > 500:
            desc = desc[:500] + "..."
        md_lines.append(f"{desc}\n")
    
    # Add transcript/content
    if transcript_type == 'summary':
        md_lines.append("## Summary\n")
    elif transcript_type == 'timestamped':
        md_lines.append("## Transcript\n")
    else:
        md_lines.append("## Transcript\n")
    
    # Format the content based on type
    if transcript_type == 'timestamped':
        formatted_content = format_timestamped_transcript(content)
    else:
        formatted_content = clean_transcript_text(content)
    
    md_lines.append(formatted_content)
    
    # Add footer
    md_lines.append("\n---\n")
    md_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write markdown file
    md_filename = txt_file.stem + '.md'
    md_path = output_dir / md_filename
    
    try:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        print(f"  ✅ Created: {md_filename}")
        return True
    except Exception as e:
        print(f"  ❌ Error writing markdown: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Convert YouTube transcript text files to formatted markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python convert_transcripts_to_markdown.py transcript_folder/
  python convert_transcripts_to_markdown.py input_dir/ --output-dir markdown_output/
  python convert_transcripts_to_markdown.py transcripts/ --no-metadata"""
    )
    
    parser.add_argument('input_dir', help='Directory containing transcript .txt files')
    parser.add_argument('--output-dir', help='Output directory for markdown files (default: input_dir + "_markdown")')
    parser.add_argument('--no-metadata', action='store_true', help='Skip fetching video metadata')
    parser.add_argument('--pattern', default='*.txt', help='File pattern to match (default: *.txt)')
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        return
    
    # Set output directory
    if args.output_dir:
        output_path = Path(args.output_dir)
    else:
        output_path = Path(str(input_path) + "_markdown")
    
    output_path.mkdir(exist_ok=True)
    print(f"Output directory: {output_path}")
    
    # Find all text files
    txt_files = list(input_path.glob(args.pattern))
    if not txt_files:
        print(f"No files matching pattern '{args.pattern}' found in {input_path}")
        return
    
    print(f"Found {len(txt_files)} transcript files to convert")
    
    # Convert each file
    successful = 0
    failed = 0
    
    for txt_file in txt_files:
        if convert_to_markdown(txt_file, output_path, fetch_metadata=not args.no_metadata):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Conversion complete!")
    print(f"Successfully converted: {successful}/{len(txt_files)} files")
    if failed > 0:
        print(f"Failed: {failed} files")
    print(f"Output directory: {output_path}")

if __name__ == "__main__":
    main()