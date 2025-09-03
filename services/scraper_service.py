import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from apify_client import ApifyClient
from dotenv import load_dotenv
import logging
from data_models import TimeFilter, ProfileData

# Set up logging - suppress verbose scraper logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Only show warnings and errors

class SocialMediaScraper:
    def __init__(self):
        load_dotenv()
        self.apify_token = os.getenv('APIFY_TOKEN')
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN not found in .env file")
        self.apify_client = ApifyClient(self.apify_token)

    def _convert_time_filter_to_apify_format(self, time_filter: TimeFilter) -> str:
        """Convert TimeFilter to Apify-compatible time format"""
        days_diff = (datetime.now() - time_filter.start_date).days
        if days_diff <= 1:
            return "1 day"
        elif days_diff <= 7:
            return "1 week"
        elif days_diff <= 30:
            return "1 month"
        elif days_diff <= 90:
            return "3 months"
        else:
            return "6 months"

    def _extract_instagram_thumbnail(self, item: Dict) -> str:
        """Extract thumbnail from Instagram post"""
        post_type = item.get('type', '').lower()
        
        if post_type == 'video':
            thumbnail_candidates = [
                item.get('displayUrl'),
                item.get('imageUrl'),
                item.get('thumbnailSrc'),
                item.get('videoViewUrl')
            ]
        elif post_type == 'sidecar':
            images_array = item.get('images', [])
            if images_array:
                thumbnail_candidates = [images_array[0], item.get('displayUrl')]
            else:
                thumbnail_candidates = [item.get('displayUrl'), item.get('imageUrl')]
        else:
            thumbnail_candidates = [
                item.get('displayUrl'),
                item.get('imageUrl'),
                item.get('thumbnailSrc')
            ]
        
        for candidate in thumbnail_candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return ''

    def _extract_facebook_thumbnail(self, media_items: List[Dict]) -> str:
        """Extract thumbnail from Facebook media items"""
        if not media_items:
            return ''
        
        for media in media_items:
            media_type = media.get('__typename', '')
            
            if media_type == 'Photo':
                thumbnail_url = media.get('thumbnail') or media.get('image', {}).get('uri')
                if thumbnail_url:
                    return thumbnail_url
            
            elif media_type == 'Video':
                thumbnail_url = media.get('thumbnail', {})
                if isinstance(thumbnail_url, dict):
                    thumbnail_url = thumbnail_url.get('uri') or thumbnail_url.get('url')
                elif isinstance(thumbnail_url, str):
                    thumbnail_url = thumbnail_url
                else:
                    thumbnail_url = media.get('previewImage', {}).get('uri')
                
                if thumbnail_url:
                    return thumbnail_url
        
        return ''

    async def scrape_instagram_profile(self, instagram_url: str) -> ProfileData:
        """Scrape Instagram profile information"""
        try:
            logger.info(f"Scraping Instagram profile: {instagram_url}")
            
            username = instagram_url.rstrip('/').split('/')[-1]
            
            run_input = {"usernames": [username]}
            run = self.apify_client.actor("dSCLg0C3YEZ83HzYX").call(run_input=run_input)
            
            if not run:
                raise RuntimeError("Failed to scrape Instagram profile")
            
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                return ProfileData(
                    username=item.get('username', username),
                    followers=item.get('followersCount', 0),
                    following=item.get('followingCount', 0),
                    posts_count=item.get('postsCount', 0),
                    platform="instagram"
                )
            
            return ProfileData(
                username=username,
                followers=0,
                following=0,
                posts_count=0,
                platform="instagram"
            )
            
        except Exception as e:
            logger.error(f"Error scraping Instagram profile: {e}")
            return ProfileData(
                username=instagram_url.rstrip('/').split('/')[-1],
                followers=0,
                following=0,
                posts_count=0,
                platform="instagram"
            )

    async def scrape_instagram_posts(self, instagram_url: str, time_filter: TimeFilter) -> List[Dict[str, Any]]:
        """Scrape Instagram posts"""
        try:
            logger.info(f"Scraping Instagram posts: {instagram_url}")
            
            time_filter_str = self._convert_time_filter_to_apify_format(time_filter)
            
            run_input = {
                "directUrls": [instagram_url],
                "resultsType": "posts",
                "resultsLimit": 5,
                "onlyPostsNewerThan": time_filter_str,
                "searchType": "hashtag",
                "addParentData": False
            }
            
            run = self.apify_client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
            
            if not run:
                raise RuntimeError("Failed to scrape Instagram posts")
            
            posts = []
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                timestamp = datetime.now()
                if item.get('timestamp'):
                    try:
                        timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                    except:
                        pass
                
                engagement = (item.get('likesCount', 0) + item.get('commentsCount', 0))
                thumbnail = self._extract_instagram_thumbnail(item)
                
                # Handle carousel posts
                all_thumbnails = []
                post_type = item.get('type', '').lower()
                
                if post_type == 'sidecar':
                    images_array = item.get('images', [])
                    all_thumbnails = [img for img in images_array if img and isinstance(img, str)]
                    if thumbnail and thumbnail not in all_thumbnails:
                        all_thumbnails.insert(0, thumbnail)
                else:
                    all_thumbnails = [thumbnail] if thumbnail else []
                
                media_type = 'video' if post_type == 'video' else 'carousel' if post_type == 'sidecar' else 'photo'
                
                post_data = {
                    'id': item.get('id', ''),
                    'platform': 'instagram',
                    'url': item.get('url', ''),
                    'caption': item.get('caption', ''),
                    'hashtags': item.get('hashtags', []),
                    'likes': item.get('likesCount', 0),
                    'comments': item.get('commentsCount', 0),
                    'shares': 0,
                    'reactions': 0,
                    'engagement': engagement,
                    'timestamp': timestamp,
                    'thumbnail': thumbnail,
                    'thumbnails': all_thumbnails,
                    'media_type': media_type,
                    'model': None,
                    'brand': None
                }
                
                posts.append(post_data)
            
            logger.info(f"Scraped {len(posts)} Instagram posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping Instagram posts: {e}")
            return []

    async def scrape_facebook_profile(self, facebook_url: str) -> ProfileData:
        """Scrape Facebook profile information"""
        try:
            logger.info(f"Scraping Facebook profile: {facebook_url}")
            
            run_input = {"startUrls": [{"url": facebook_url}]}
            run = self.apify_client.actor("4Hv5RhChiaDk6iwad").call(run_input=run_input)
            
            if not run:
                raise RuntimeError("Failed to scrape Facebook profile")
            
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                return ProfileData(
                    username=item.get('name', facebook_url.split('/')[-1]),
                    followers=item.get('followers', 0),
                    following=0,
                    posts_count=0,
                    platform="facebook"
                )
            
            return ProfileData(
                username=facebook_url.split('/')[-1],
                followers=0,
                following=0,
                posts_count=0,
                platform="facebook"
            )
            
        except Exception as e:
            logger.error(f"Error scraping Facebook profile: {e}")
            return ProfileData(
                username=facebook_url.split('/')[-1],
                followers=0,
                following=0,
                posts_count=0,
                platform="facebook"
            )

    async def scrape_facebook_posts(self, facebook_url: str, time_filter: TimeFilter) -> List[Dict[str, Any]]:
        """Scrape Facebook posts"""
        try:
            logger.info(f"Scraping Facebook posts: {facebook_url}")
            
            time_filter_str = self._convert_time_filter_to_apify_format(time_filter)
            
            run_input = {
                "startUrls": [{"url": facebook_url}],
                "resultsLimit": 5,
                "onlyPostsNewerThan": time_filter_str,
                "captionText": False
            }
            
            run = self.apify_client.actor("KoJrdxJCTtpon81KY").call(run_input=run_input)
            
            if not run:
                raise RuntimeError("Failed to scrape Facebook posts")
            
            posts = []
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                timestamp = datetime.now()
                if item.get('time'):
                    try:
                        timestamp = datetime.fromisoformat(item['time'].replace('Z', '+00:00'))
                    except:
                        pass
                
                engagement = (item.get('likes', 0) + 
                            item.get('comments', 0) + 
                            item.get('shares', 0) + 
                            item.get('topReactionsCount', 0))
                
                text = item.get('text', '')
                hashtags = []
                if text:
                    words = text.split()
                    hashtags = [word[1:] for word in words if word.startswith('#')]
                
                media_items = item.get('media', [])
                main_thumbnail = self._extract_facebook_thumbnail(media_items)
                
                all_thumbnails = []
                for media in media_items:
                    thumb = self._extract_facebook_thumbnail([media])
                    if thumb and thumb not in all_thumbnails:
                        all_thumbnails.append(thumb)
                
                post_data = {
                    'id': item.get('postId', ''),
                    'platform': 'facebook',
                    'url': item.get('topLevelUrl', ''),
                    'text': text,
                    'caption': text,
                    'hashtags': hashtags,
                    'likes': item.get('likes', 0),
                    'comments': item.get('comments', 0),
                    'shares': item.get('shares', 0),
                    'reactions': item.get('topReactionsCount', 0),
                    'engagement': engagement,
                    'timestamp': timestamp,
                    'thumbnail': main_thumbnail,
                    'thumbnails': all_thumbnails,
                    'media_type': self._determine_media_type(media_items),
                    'model': None,
                    'brand': None
                }
                posts.append(post_data)
            
            logger.info(f"Scraped {len(posts)} Facebook posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping Facebook posts: {e}")
            return []

    def _determine_media_type(self, media_items: List[Dict]) -> str:
        """Determine the primary media type of the post"""
        if not media_items:
            return 'text'
        
        media_types = [item.get('__typename', '').lower() for item in media_items]
        
        if 'video' in media_types:
            return 'video'
        elif 'photo' in media_types:
            return 'photo' if len(media_items) == 1 else 'carousel'
        else:
            return 'mixed'