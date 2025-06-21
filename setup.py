#!/usr/bin/env python3
"""
Setup script for YouTube Playlist to Markdown

This script helps with initial setup and dependency installation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.7 or higher."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        print(f"   You have Python {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_pip():
    """Check if pip is installed."""
    try:
        import pip
        print("✅ pip is installed")
        return True
    except ImportError:
        print("❌ pip is not installed")
        print("   Please install pip first")
        return False

def install_requirements():
    """Install Python requirements."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        print("   Try running: pip install -r requirements.txt")
        return False

def check_ytdlp():
    """Check if yt-dlp is installed."""
    if shutil.which("yt-dlp"):
        print("✅ yt-dlp is installed")
        return True
    elif shutil.which("youtube-dl"):
        print("⚠️  youtube-dl is installed (yt-dlp is recommended)")
        return True
    else:
        print("❌ yt-dlp is not installed")
        print("   Install with: pip install yt-dlp")
        print("   Or visit: https://github.com/yt-dlp/yt-dlp#installation")
        return False

def setup_env_file():
    """Create .env file from template."""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists(".env.example"):
        try:
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from template")
            print("   ⚠️  Please edit .env and add your GEMINI_API_KEY")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example not found")
        return False

def check_gemini_api_key():
    """Check if Gemini API key is set."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key and api_key != "your_gemini_api_key_here":
            print("✅ GEMINI_API_KEY is configured")
            return True
        else:
            print("⚠️  GEMINI_API_KEY not configured")
            print("   1. Get your API key from: https://makersuite.google.com/app/apikey")
            print("   2. Add it to your .env file")
            return False
    except ImportError:
        print("⚠️  Cannot check API key (dotenv not installed yet)")
        return False

def main():
    """Run setup process."""
    print("YouTube Playlist to Markdown - Setup")
    print("====================================\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check pip
    if not check_pip():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️  Setup completed with warnings")
        sys.exit(1)
    
    # Check yt-dlp
    ytdlp_ok = check_ytdlp()
    
    # Setup .env file
    env_ok = setup_env_file()
    
    # Check API key
    api_key_ok = check_gemini_api_key()
    
    # Summary
    print("\n" + "="*50)
    print("Setup Summary")
    print("="*50)
    
    if ytdlp_ok and env_ok:
        print("✅ Setup completed successfully!")
        
        if not api_key_ok:
            print("\n⚠️  Don't forget to add your GEMINI_API_KEY to .env")
        
        print("\n🚀 You're ready to start!")
        print("   Try: python youtube_playlist_to_markdown.py YOUR_PLAYLIST_URL")
        print("   Or:  python example.py (to see usage examples)")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()