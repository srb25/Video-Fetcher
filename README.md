# Multi-Platform Video Downloader

A web application that allows you to download videos from multiple platforms including YouTube, Instagram, Facebook, Reddit, X (Twitter), and Zoom at various resolutions (360p, 480p, 720p, 1080p or higher if available).

## Features

- Support for multiple platforms
- Quality selection (360p, 480p, 720p, 1080p or higher if available)
- Progress tracking for downloads
- Modern and responsive UI
- Easy to deploy for free

## Installation

### Local Development

1. Clone the repository
2. Install dependencies
   ```
   pip install -r requirements.txt
   ```
3. Install FFmpeg (required for merging audio and video):
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **Mac**: `brew install ffmpeg`
   - **Linux**: `apt-get install ffmpeg` or equivalent for your distro
4. Run the application
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser

## Free Deployment Options

### Deploy to PythonAnywhere

1. Create a free [PythonAnywhere](https://www.pythonanywhere.com/) account
2. Go to the "Web" tab and click "Add a new web app"
3. Choose Flask and Python 3.9+
4. In the "Code" section, set the source code directory to your project
5. Set the WSGI configuration file to point to your app:
   ```python
   import sys
   path = '/home/yourusername/your-project-directory'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```
6. Install required packages from `requirements.txt` using PythonAnywhere's "Consoles" tab
7. Ensure FFmpeg is available (check with PythonAnywhere support if needed)
8. Reload your web app

### Deploy to Render

1. Create a free [Render](https://render.com/) account
2. Connect your GitHub repository
3. Create a new Web Service
4. Select your repository
5. Set the build command to `pip install -r requirements.txt`
6. Set the start command to `gunicorn app:app`
7. Deploy your app

## How It Works

This application uses yt-dlp, a powerful command-line tool for downloading videos from various platforms. The Flask web server provides a user-friendly interface for selecting video quality and downloading content.

When you select a quality option (360p, 480p, 720p, 1080p), the application automatically downloads both the video and audio streams at the best possible quality for that resolution, then merges them together to provide a complete video file with sound. This ensures you get both high-quality video and audio regardless of the selected resolution.

## Troubleshooting

### No Audio in Downloaded Videos

If you're experiencing videos downloading without audio:

1. **Check FFmpeg Installation**: The app requires FFmpeg to merge audio and video streams. Make sure it's installed and available in your PATH.
   ```
   ffmpeg -version
   ```

2. **Try "Best Quality" Option**: The "Best quality" option often provides the most reliable audio+video combination.

3. **Check Temporary Directory**: Ensure your system's temporary directory has enough space and permissions.

4. **Platform Limitations**: Some platforms may restrict certain content or formats. Try downloading from another source if possible.

## Limitations

- Free deployment options may have CPU/memory/bandwidth limitations
- Some websites may block or limit downloads from their platforms
- Video availability and format options depend on the source platform

## Legal Disclaimer

This tool is designed for downloading content that you have the right to download. Please respect copyright laws and terms of service for all platforms. Do not use this tool to download copyrighted content without appropriate permissions.

## License

MIT 