from flask import Flask, render_template, request, send_file, jsonify
import os
import tempfile
import yt_dlp
import re
import uuid
from urllib.parse import urlparse
import random
import config

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Dictionary to store download status
download_tasks = {}

def get_random_proxy():
    """Return a random proxy from the list, or None if proxy usage is disabled"""
    if not config.USE_PROXY or not config.PROXY_LIST:
        return None
    return random.choice(config.PROXY_LIST)

def apply_proxy_settings(ydl_opts):
    """Apply proxy settings to a yt-dlp options dictionary if enabled"""
    if config.USE_PROXY:
        proxy = get_random_proxy()
        if proxy:
            ydl_opts['proxy'] = proxy
            ydl_opts['socket_timeout'] = config.SOCKET_TIMEOUT
            return proxy
    return None

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_platform(url):
    if not is_valid_url(url):
        return "invalid"
    
    domain = urlparse(url).netloc.lower()
    
    if any(x in domain for x in ["youtube", "youtu.be"]):
        return "youtube"
    elif "instagram" in domain:
        return "instagram"
    elif "facebook" in domain or "fb.com" in domain:
        return "facebook"
    elif "reddit" in domain:
        return "reddit"
    elif any(x in domain for x in ["twitter", "x.com"]):
        return "twitter"
    elif "zoom.us" in domain:
        return "zoom"
    else:
        return "unknown"

def get_available_formats(url):
    try:
        ydl_opts = {'quiet': True}
        proxy = apply_proxy_settings(ydl_opts)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # Always add a "best" option first
            formats.append({
                'format_id': 'bestvideo+bestaudio/best',
                'label': 'Best quality'
            })
            
            # Define formats that ensure both video and audio
            format_options = [
                {'height': 360, 'format_id': 'bestvideo[height<=360]+bestaudio/best[height<=360]', 'label': '360p'},
                {'height': 480, 'format_id': 'bestvideo[height<=480]+bestaudio/best[height<=480]', 'label': '480p'},
                {'height': 720, 'format_id': 'bestvideo[height<=720]+bestaudio/best[height<=720]', 'label': '720p'},
                {'height': 1080, 'format_id': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]', 'label': '1080p'}
            ]
            
            # Add formats based on what's available
            available_heights = set()
            for f in info.get('formats', []):
                if f.get('height') and f.get('height') > 0:
                    available_heights.add(f.get('height'))
            
            print(f"Available heights: {available_heights}")
            
            if not available_heights:
                # If no heights available, offer all standard options
                for option in format_options:
                    formats.append({
                        'format_id': option['format_id'],
                        'label': option['label']
                    })
            else:
                # Offer only resolutions that are available (or lower)
                for option in format_options:
                    # Check if this or any lower resolution is available
                    matching_heights = [h for h in available_heights if h <= option['height']]
                    if matching_heights:
                        formats.append({
                            'format_id': option['format_id'],
                            'label': option['label']
                        })
            
            return formats
    except Exception as e:
        print(f"Error in format selection: {str(e)}")
        # Fallback to basic formats in case of error
        return [
            {'format_id': 'bestvideo+bestaudio/best', 'label': 'Best quality'},
            {'format_id': 'bestvideo[height<=360]+bestaudio/best', 'label': '360p'},
            {'format_id': 'bestvideo[height<=480]+bestaudio/best', 'label': '480p'},
            {'format_id': 'bestvideo[height<=720]+bestaudio/best', 'label': '720p'},
            {'format_id': 'bestvideo[height<=1080]+bestaudio/best', 'label': '1080p'}
        ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-info', methods=['POST'])
def get_info():
    url = request.json.get('url', '')
    platform = get_platform(url)
    
    if platform == "invalid":
        return jsonify({"status": "error", "message": "Invalid URL"})
    
    if platform == "unknown":
        return jsonify({"status": "error", "message": "Unsupported platform"})
    
    try:
        # Set up options with detailed debugging
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True  # Don't immediately fail on errors
        }
        
        proxy = apply_proxy_settings(ydl_opts)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Attempting to extract info for: {url}" + (f" using proxy: {proxy}" if proxy else ""))
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print(f"No info extracted for: {url}")
                return jsonify({"status": "error", "message": "Could not extract video information. The video might be private, removed, or region-restricted."})
            
            formats = []
            
            # Always add a "best" option first
            formats.append({
                'format_id': 'bestvideo+bestaudio/best',
                'label': 'Best quality'
            })
            
            # Get available heights from the video
            available_heights = set()
            for f in info.get('formats', []):
                if f.get('height') and f.get('height') > 0:
                    available_heights.add(f.get('height'))
            
            print(f"Available heights: {available_heights}")
            
            # Common resolutions to offer
            target_heights = [360, 480, 720, 1080]
            
            # If there are no valid heights, offer standard options
            if not available_heights:
                print("No valid heights found, offering standard options")
                for height in target_heights:
                    formats.append({
                        'format_id': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
                        'label': f"{height}p"
                    })
            else:
                # Determine which resolutions are available (rounding to standard values)
                added_heights = set()
                for target in target_heights:
                    # Find the closest available height that's not higher than target
                    closest = [h for h in available_heights if h <= target]
                    if closest:
                        max_height = max(closest)
                        if max_height not in added_heights:
                            formats.append({
                                'format_id': f'bestvideo[height<={target}]+bestaudio/best[height<={target}]',
                                'label': f"{target}p"
                            })
                            added_heights.add(max_height)
            
            print(f"Offering formats: {formats}")
            return jsonify({
                "status": "success",
                "platform": platform,
                "formats": formats,
                "title": info.get('title', 'Unknown Title')
            })
    except Exception as e:
        print(f"Error extracting info: {str(e)}")
        error_message = str(e)
        if "This video is not available" in error_message:
            error_message = "This video is not available. It may be private, removed, or region-restricted."
        elif "Sign in to confirm your age" in error_message:
            error_message = "Age-restricted video. Cannot process this content."
        elif "is not a valid URL" in error_message:
            error_message = "The URL is invalid or not supported."
        elif "Unsupported URL" in error_message:
            error_message = "This URL or platform is not supported."
        return jsonify({"status": "error", "message": error_message})

@app.route('/api/download', methods=['POST'])
def download_video():
    url = request.json.get('url', '')
    format_id = request.json.get('format_id', config.DEFAULT_FORMAT)
    title = request.json.get('title', '')
    
    if not url:
        return jsonify({"status": "error", "message": "URL is required"})
    
    # Always ensure we have audio
    if 'bestaudio' not in format_id and '+bestaudio' not in format_id:
        format_id = f"{format_id}+bestaudio/best"
    
    task_id = str(uuid.uuid4())
    download_tasks[task_id] = {
        "status": "started", 
        "progress": 0,
        "title": title
    }
    
    try:
        # Create a more reliable storage directory - use absolute path to avoid issues
        storage_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'downloads')
        os.makedirs(storage_dir, exist_ok=True)
        print(f"Using storage directory: {storage_dir}")
        
        # Use task_id in filename to ensure uniqueness
        output_path = os.path.join(storage_dir, f"{task_id}.%(ext)s")
        
        ydl_opts = {
            'format': format_id,
            'outtmpl': output_path,
            'progress_hooks': [lambda d: update_progress(task_id, d)],
            'merge_output_format': config.MERGE_OUTPUT_FORMAT,
            'postprocessor_args': ['-movflags', 'faststart'],  # Optimize for streaming
            'noplaylist': True,  # Only download the video, not playlists
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,  # Don't ignore errors during download
            # Add FFmpeg-specific options to ensure audio is included
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Ensure we have FFmpeg for merging
            'prefer_ffmpeg': True,
        }
        
        # Apply proxy settings
        proxy = apply_proxy_settings(ydl_opts)
        if proxy:
            print(f"Using proxy for download: {proxy}")
        
        # Get video info if no title was provided
        if not title:
            try:
                info_opts = {'quiet': True}
                apply_proxy_settings(info_opts)
                with yt_dlp.YoutubeDL(info_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and 'title' in info:
                        download_tasks[task_id]['title'] = info['title']
                        print(f"Video title: {info['title']}")
            except Exception as e:
                print(f"Error getting video title: {str(e)}")
        
        # Store the output path for later reference
        download_tasks[task_id]['output_dir'] = storage_dir
        download_tasks[task_id]['output_template'] = output_path
        
        # Start download in a new thread
        import threading
        thread = threading.Thread(target=download_thread, args=(url, ydl_opts, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "task_id": task_id
        })
        
    except Exception as e:
        download_tasks[task_id] = {"status": "error", "error": str(e)}
        return jsonify({"status": "error", "message": str(e)})

def update_progress(task_id, d):
    if d['status'] == 'downloading':
        try:
            # Try to get percentage from _percent_str
            p = d.get('_percent_str', '0%').strip()
            if p.endswith('%'):
                try:
                    download_tasks[task_id]['progress'] = float(p[:-1])
                except:
                    # Fallback to calculating percentage
                    total_bytes = d.get('total_bytes')
                    downloaded_bytes = d.get('downloaded_bytes')
                    if total_bytes and downloaded_bytes:
                        download_tasks[task_id]['progress'] = min(100, downloaded_bytes * 100 / total_bytes)
                    else:
                        # If we still can't calculate, use a default
                        download_tasks[task_id]['progress'] = 0
        except:
            # In case of any error, don't crash
            pass
    
    elif d['status'] == 'finished':
        download_tasks[task_id]['status'] = 'processing'
        download_tasks[task_id]['progress'] = 100
        
        # Store the downloaded filename
        filename = d.get('filename', '')
        if filename:
            download_tasks[task_id]['filename'] = filename
            print(f"Download finished: {filename}")
            
            # Verify the file exists
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"File size: {file_size} bytes")
                if file_size > 0:
                    print("File is valid")
                else:
                    print("WARNING: File is empty")
            else:
                print(f"WARNING: File does not exist: {filename}")

@app.route('/api/download-file/<task_id>')
def download_file(task_id):
    if task_id not in download_tasks:
        return jsonify({"status": "error", "message": "Download task not found"})
    
    if download_tasks[task_id]['status'] != 'finished':
        return jsonify({"status": "error", "message": "File not ready yet"})
    
    filename = download_tasks[task_id].get('filename')
    if not filename:
        # Try to find the file by pattern matching if filename is not stored
        try:
            output_dir = download_tasks[task_id].get('output_dir')
            if output_dir and os.path.exists(output_dir):
                pattern = f"{task_id}.*"
                matching_files = [f for f in os.listdir(output_dir) if f.startswith(task_id)]
                if matching_files:
                    filename = os.path.join(output_dir, matching_files[0])
                    print(f"Found file by pattern matching: {filename}")
                    download_tasks[task_id]['filename'] = filename
        except Exception as e:
            print(f"Error finding file by pattern: {str(e)}")
    
    if not filename or not os.path.exists(filename):
        error_msg = f"File not found for task {task_id}"
        print(error_msg)
        download_tasks[task_id]['status'] = 'error'
        download_tasks[task_id]['error'] = 'File was removed or not properly saved'
        return jsonify({
            "status": "error", 
            "message": "File was removed or not properly saved. Please try downloading again."
        })
    
    try:
        # Get file info for better attachment name
        file_size = os.path.getsize(filename)
        if file_size == 0:
            return jsonify({"status": "error", "message": "File is empty. The download may have failed."})
        
        # Get a better filename for the download
        original_title = download_tasks[task_id].get('title', 'video')
        # Clean up the title to make it a valid filename
        safe_title = re.sub(r'[^\w\s-]', '', original_title).strip().replace(' ', '_')
        if not safe_title:
            safe_title = 'video'
        
        # Get the extension from the original file
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = '.mp4'  # Default extension if none is found
        
        # Better filename for the user
        download_name = f"{safe_title}{ext}"
        
        # Send the file with a proper attachment name
        return send_file(
            filename, 
            as_attachment=True,
            download_name=download_name,
            max_age=0  # Don't cache the file
        )
    except Exception as e:
        print(f"Error sending file: {str(e)}")
        return jsonify({"status": "error", "message": f"Error accessing file: {str(e)}"})

def download_thread(url, ydl_opts, task_id):
    try:
        # Ensure ffmpeg is available for merging
        print(f"Starting download with options: {ydl_opts}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First try with the requested format
            try:
                # Extract info first to check if we need special handling
                info = ydl.extract_info(url, download=False)
                if info:
                    # Store the title if available
                    if 'title' in info and info['title']:
                        download_tasks[task_id]['title'] = info['title']
                
                # Now do the actual download
                ydl.download([url])
                
                # Verify the file exists after download
                output_dir = download_tasks[task_id].get('output_dir')
                if output_dir and os.path.exists(output_dir):
                    pattern = f"{task_id}.*"
                    matching_files = [f for f in os.listdir(output_dir) if f.startswith(task_id)]
                    if matching_files:
                        filename = os.path.join(output_dir, matching_files[0])
                        download_tasks[task_id]['filename'] = filename
                        print(f"Download successful: {filename}")
                        if os.path.exists(filename) and os.path.getsize(filename) > 0:
                            download_tasks[task_id]['status'] = 'finished'
                            return
                
                # If we didn't find the file or it was empty, try again with a different format
                if download_tasks[task_id]['status'] != 'finished':
                    raise Exception("Download completed but file was not found or empty")
                    
            except Exception as format_error:
                # If the specific format fails, try with best format
                try:
                    # Log the original error
                    print(f"Error with format {ydl_opts['format']}: {str(format_error)}")
                    download_tasks[task_id]['status'] = 'retrying'
                    download_tasks[task_id]['progress'] = 0
                    
                    # Try with a simpler format option that ensures both audio and video
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        ydl2.download([url])
                    
                    # Verify the file exists after download
                    output_dir = download_tasks[task_id].get('output_dir')
                    if output_dir and os.path.exists(output_dir):
                        pattern = f"{task_id}.*"
                        matching_files = [f for f in os.listdir(output_dir) if f.startswith(task_id)]
                        if matching_files:
                            filename = os.path.join(output_dir, matching_files[0])
                            download_tasks[task_id]['filename'] = filename
                            print(f"Download successful (retry): {filename}")
                            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                                download_tasks[task_id]['status'] = 'finished'
                                return
                    
                    # If we still didn't find the file, raise an error
                    raise Exception("Retry download completed but file was not found or empty")
                    
                except Exception as e:
                    # If that also fails, report the error
                    download_tasks[task_id]['status'] = 'error'
                    download_tasks[task_id]['error'] = f"Format error: {str(e)}"
    except Exception as e:
        download_tasks[task_id]['status'] = 'error'
        download_tasks[task_id]['error'] = str(e)

@app.route('/api/status/<task_id>')
def get_status(task_id):
    if task_id not in download_tasks:
        return jsonify({"status": "not_found"})
    
    response_data = {}
    # Create a copy of task data, not the actual reference
    for key, value in download_tasks[task_id].items():
        # Include all fields except potentially sensitive ones
        if key not in ['output_dir', 'output_template']:
            response_data[key] = value
    
    return jsonify(response_data)

# Create downloads directory at startup
if not os.path.exists('downloads'):
    os.makedirs('downloads', exist_ok=True)
    print("Created downloads directory")

if __name__ == '__main__':
    # Check if FFmpeg is available
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=False)
        print("FFmpeg is available - audio and video merging will work correctly.")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("WARNING: FFmpeg is not available in PATH. Audio and video merging may not work correctly.")
        print("Please install FFmpeg to ensure videos have both audio and video streams.")
    
    # Configuration for production
    # When running directly, use 0.0.0.0 to listen on all interfaces
    # But never run with debug=True in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# For production WSGI servers (Gunicorn, uWSGI, etc.)
# This allows the application to be imported
application = app 