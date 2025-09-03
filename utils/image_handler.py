import requests
import hashlib
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 3600  # 1 hour

    async def get_proxied_image(self, url: str) -> bytes:
        """Get proxied image with caching"""
        try:
            # Create cache key
            cache_key = hashlib.md5(url.encode()).hexdigest()
            current_time = time.time()
            
            # Check cache
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if current_time - timestamp < self.cache_duration:
                    return cached_data
            
            # Fetch image with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site'
            }
            
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            
            if response.status_code == 200:
                content = response.content
                
                # Cache the image
                self.cache[cache_key] = (content, current_time)
                
                # Clean old cache entries (keep only last 100)
                if len(self.cache) > 100:
                    oldest_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k][1])[:50]
                    for key in oldest_keys:
                        del self.cache[key]
                
                return content
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Image proxy error for {url}: {e}")
            raise

    def generate_placeholder_image(self) -> bytes:
        """Generate SVG placeholder for failed images"""
        svg = '''
        <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100" fill="#f3f4f6"/>
            <rect x="20" y="20" width="60" height="60" fill="#e5e7eb" stroke="#d1d5db" stroke-width="2" rx="8"/>
            <circle cx="35" cy="35" r="8" fill="#9ca3af"/>
            <polygon points="20,70 35,50 50,60 65,45 80,70" fill="#9ca3af"/>
            <text x="50" y="85" text-anchor="middle" font-family="Arial, sans-serif" font-size="8" fill="#6b7280">Image Error</text>
        </svg>
        '''.encode('utf-8')
        return svg