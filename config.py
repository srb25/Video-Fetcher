# Configuration settings for the Video Fetcher application

# Proxy configurations
# Update this list regularly as public proxies can change frequently
# Format: 'protocol://ip:port'
PROXY_LIST = [
    # India proxies (high priority for Indian content)
    'socks5://103.48.68.36:9050',
    'socks5://103.240.161.101:6667',
    'socks5://103.149.53.120:59166',
    'socks5://103.69.216.249:50820',
    
    # Global proxies (fallback)
    'socks5://51.79.52.80:3080',
    'socks5://195.154.255.118:15001',
    'socks5://184.178.172.5:15303',
    'socks5://184.178.172.14:4145',
    'socks5://72.195.34.58:4145',
    'socks5://174.77.111.197:4145',
]

# Proxy configuration
USE_PROXY = True  # Set to False to disable proxy usage globally
PROXY_TIMEOUT = 30  # Seconds to wait for proxy connection

# Download settings
DEFAULT_FORMAT = 'bestvideo+bestaudio/best'
MERGE_OUTPUT_FORMAT = 'mp4'
SOCKET_TIMEOUT = 30 