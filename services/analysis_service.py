import os
from openai import OpenAI
import base64
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import json
import logging
from data_models import TimeFilter
from dotenv import load_dotenv
import asyncio
from PIL import Image
import io

load_dotenv(override=True)

# Set up logging - suppress verbose logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Only show warnings and errors

class AnalysisService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = OpenAI(api_key=api_key)

    async def classify_posts_with_vision(self, posts: List[Dict[str, Any]], keywords: List[str], 
                                       platform: str, brand_name: str, 
                                       reference_images: Dict[str, List[str]] = None) -> List[Dict[str, Any]]:
        """Classify posts using both text and vision analysis"""
        logger.info(f"Starting classification for {brand_name} on {platform}")
        logger.info(f"Posts to classify: {len(posts)}")
        
        classified_posts = []
        reference_images = reference_images or {}
        
        for i, post in enumerate(posts):
            logger.info(f"Classifying post {i+1}/{len(posts)} for {brand_name}")
            classified_post = await self._classify_single_post_with_vision(
                post, keywords, platform, brand_name, reference_images
            )
            classified_posts.append(classified_post)
            await asyncio.sleep(0.5)  # Rate limiting
        
        return classified_posts

    async def _classify_single_post_with_vision(self, post: Dict[str, Any], keywords: List[str], 
                                              platform: str, brand_name: str, 
                                              reference_images: Dict[str, List[str]]) -> Dict[str, Any]:
        """Classify a single post using GPT-4 Vision"""
        try:
            # Extract text content
            text_content, hashtags = self._extract_text_content(post, platform)
            
            # Check if we have enough content for classification
            has_text = bool(text_content.strip() or hashtags)
            has_image = bool(post.get('thumbnail'))
            
            if not has_text and not has_image:
                post['model'] = 'unclassified'
                post['classification_reason'] = 'No text or image content available'
                post['classification_confidence'] = 0
                return post
            
            # Try text-based classification first if we have text
            if has_text:
                classification = await self._classify_with_text_and_vision(
                    text_content, hashtags, keywords, brand_name, post, reference_images
                )
            else:
                # Image-only classification
                classification = await self._classify_with_image_only(
                    post, keywords, brand_name, reference_images
                )
            
            # Apply classification to post
            post['model'] = classification.get('model', 'unclassified')
            post['classification_reason'] = classification.get('reason', 'Analysis completed')
            post['classification_confidence'] = classification.get('confidence', 0)
            
            return post
            
        except Exception as e:
            logger.error(f"Error classifying post: {e}")
            post['model'] = 'unclassified'
            post['classification_reason'] = f'Classification error: {str(e)}'
            post['classification_confidence'] = 0
            return post

    async def _classify_with_text_and_vision(self, text_content: str, hashtags: List[str],
                                           keywords: List[str], brand_name: str, 
                                           post: Dict[str, Any], 
                                           reference_images: Dict[str, List[str]]) -> Dict[str, Any]:
        """Classify using both text and vision"""
        try:
            # Prepare message content
            hashtags_text = ' '.join([f'#{tag}' for tag in hashtags]) if hashtags else 'No hashtags'
            
            prompt = f"""
            VEHICLE MODEL CLASSIFICATION TASK
            
            BRAND: {brand_name}
            TARGET MODELS: {', '.join(keywords)}
            
            POST CONTENT:
            Text: "{text_content[:800]}"
            Hashtags: {hashtags_text}
            
            CLASSIFICATION RULES:
            1. If text mentions any TARGET MODEL exactly or partially, classify as that model
            2. If text mentions other vehicle models not in target list, use that model name
            3. If text is automotive-related but no specific model, classify as "general_automotive"
            4. If text is not automotive-related, classify as "non_automotive"
            5. If unclear, classify as "unclassified"
            
            If an image is provided, use it to support your text-based classification.
            
            RESPOND IN JSON FORMAT:
            {{
                "model": "exact_model_name_or_category",
                "reason": "detailed_explanation_with_evidence",
                "confidence": confidence_score_1_to_100
            }}
            """
            
            message_content = [{"type": "text", "text": prompt}]
            
            # Add post image if available
            if post.get('thumbnail'):
                image_b64 = await self._download_and_encode_image(post['thumbnail'])
                if image_b64:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    })
            
            # Add reference images (up to 6 total to stay within limits)
            ref_count = 0
            for model, image_paths in reference_images.items():
                if ref_count >= 6:
                    break
                for image_path in image_paths[:2]:  # Max 2 per model
                    try:
                        ref_image_b64 = self._encode_local_image(image_path)
                        if ref_image_b64:
                            message_content.extend([
                                {"type": "text", "text": f"Reference for {model}:"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{ref_image_b64}"}
                                }
                            ])
                            ref_count += 1
                            if ref_count >= 6:
                                break
                    except Exception as e:
                        logger.warning(f"Failed to load reference image {image_path}: {e}")
                        continue
            
            # Call OpenAI GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": message_content}],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse response
            return self._parse_classification_response(response.choices[0].message.content, keywords)
            
        except Exception as e:
            logger.error(f"Error in text+vision classification: {e}")
            return {
                "model": "unclassified",
                "reason": f"Classification failed: {str(e)}",
                "confidence": 0
            }

    async def _classify_with_image_only(self, post: Dict[str, Any], keywords: List[str], 
                                      brand_name: str, reference_images: Dict[str, List[str]]) -> Dict[str, Any]:
        """Classify using only image analysis"""
        try:
            post_image_url = post.get('thumbnail')
            if not post_image_url:
                return {
                    "model": "unclassified",
                    "reason": "No image available for analysis",
                    "confidence": 0
                }
            
            # Download post image
            post_image_b64 = await self._download_and_encode_image(post_image_url)
            if not post_image_b64:
                return {
                    "model": "unclassified",
                    "reason": "Failed to download post image",
                    "confidence": 0
                }
            
            prompt = f"""
            VISION-ONLY VEHICLE MODEL CLASSIFICATION
            
            BRAND: {brand_name}
            TARGET MODELS: {', '.join(keywords)}
            
            TASK: Identify the vehicle model in the main image by comparing with reference images.
            
            ANALYSIS INSTRUCTIONS:
            1. Examine the main image for vehicle features
            2. Compare with reference images for each model
            3. Look for distinctive design elements, body shape, badges, grilles
            4. Consider overall styling and proportions
            
            RESPOND IN JSON FORMAT:
            {{
                "model": "most_matching_model_or_unclassified",
                "reason": "detailed_visual_comparison_explanation",
                "confidence": confidence_score_1_to_100
            }}
            """
            
            message_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{post_image_b64}"}
                }
            ]
            
            # Add reference images
            for model, image_paths in reference_images.items():
                for image_path in image_paths[:2]:
                    try:
                        ref_image_b64 = self._encode_local_image(image_path)
                        if ref_image_b64:
                            message_content.extend([
                                {"type": "text", "text": f"Reference for {model}:"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{ref_image_b64}"}
                                }
                            ])
                    except Exception as e:
                        logger.warning(f"Failed to load reference image {image_path}: {e}")
                        continue
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": message_content}],
                max_tokens=300,
                temperature=0.1
            )
            
            return self._parse_classification_response(response.choices[0].message.content, keywords)
            
        except Exception as e:
            logger.error(f"Error in image-only classification: {e}")
            return {
                "model": "unclassified",
                "reason": f"Image analysis failed: {str(e)}",
                "confidence": 0
            }

    def _extract_text_content(self, post: Dict[str, Any], platform: str) -> tuple:
        """Extract text content and hashtags from post"""
        text_content = ""
        hashtags = []
        
        if platform == "instagram":
            text_content = post.get('caption', '') or ''
            hashtags = post.get('hashtags', [])
        else:  # Facebook
            text_content = post.get('text', '') or post.get('caption', '') or ''
            if text_content:
                words = text_content.split()
                hashtags = [word[1:] for word in words if word.startswith('#')]
        
        return text_content, hashtags

    def _parse_classification_response(self, response: str, keywords: List[str]) -> Dict[str, Any]:
        """Parse LLM response and extract classification"""
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                classification = json.loads(json_str)
                
                model = classification.get('model', 'unclassified').strip()
                reason = classification.get('reason', 'No reason provided')
                confidence = min(100, max(0, int(classification.get('confidence', 0))))
                
                # Validate model against keywords
                if model.lower() in [k.lower() for k in keywords]:
                    exact_match = next(k for k in keywords if k.lower() == model.lower())
                    return {
                        "model": exact_match,
                        "reason": reason,
                        "confidence": confidence
                    }
                else:
                    return {
                        "model": model,
                        "reason": reason,
                        "confidence": confidence
                    }
            
            logger.warning(f"No valid JSON in LLM response: {response[:200]}")
            return {
                "model": "unclassified",
                "reason": "Failed to parse LLM response",
                "confidence": 0
            }
            
        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return {
                "model": "unclassified", 
                "reason": f"Parse error: {str(e)}",
                "confidence": 0
            }

    async def _download_and_encode_image(self, image_url: str) -> Optional[str]:
        """Download image from URL and encode as base64"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                
                # Convert RGBA to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    if image.mode in ('RGBA', 'LA'):
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                
                # Resize if too large
                if image.width > 1024 or image.height > 1024:
                    image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return None

    def _encode_local_image(self, image_path: str) -> Optional[str]:
        """Encode local image file as base64"""
        try:
            with open(image_path, 'rb') as f:
                image = Image.open(f)
                
                # Convert RGBA to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    if image.mode in ('RGBA', 'LA'):
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                
                # Resize if too large
                if image.width > 512 or image.height > 512:
                    image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Error encoding local image {image_path}: {e}")
            return None

    def calculate_engagement_metrics(self, posts: List[Dict[str, Any]], 
                                   keywords: List[str]) -> Dict[str, Any]:
        """Calculate engagement metrics for posts"""
        if not posts:
            return {"instagram": {}, "facebook": {}, "overall": {}}
        
        # Separate by platform
        instagram_posts = [p for p in posts if p.get('platform') == 'instagram']
        facebook_posts = [p for p in posts if p.get('platform') == 'facebook']
        
        # Calculate metrics for each platform
        instagram_metrics = self._calculate_platform_metrics(instagram_posts, keywords)
        facebook_metrics = self._calculate_platform_metrics(facebook_posts, keywords)
        overall_metrics = self._calculate_platform_metrics(posts, keywords)
        
        return {
            "instagram": instagram_metrics,
            "facebook": facebook_metrics,
            "overall": overall_metrics
        }

    def _calculate_platform_metrics(self, posts: List[Dict[str, Any]], 
                                  keywords: List[str]) -> Dict[str, Any]:
        """Calculate metrics for a specific platform"""
        if not posts:
            return {
                "total_posts": 0,
                "total_engagement": 0,
                "average_engagement": 0,
                "model_breakdown": {}
            }
        
        total_posts = len(posts)
        total_engagement = sum(post.get('engagement', 0) for post in posts)
        average_engagement = total_engagement / total_posts if total_posts > 0 else 0
        
        # Model breakdown
        model_breakdown = {}
        all_models = set(post.get('model', '').strip() for post in posts if post.get('model', '').strip())
        
        for model in all_models:
            model_posts = [p for p in posts if p.get('model', '').strip().lower() == model.lower()]
            if model_posts:
                model_engagement = sum(post.get('engagement', 0) for post in model_posts)
                model_breakdown[model] = {
                    "posts_count": len(model_posts),
                    "total_engagement": model_engagement,
                    "average_engagement": model_engagement / len(model_posts),
                    "engagement_rate": (model_engagement / total_engagement * 100) if total_engagement > 0 else 0,
                    "posts": model_posts
                }
        
        return {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "average_engagement": average_engagement,
            "model_breakdown": model_breakdown
        }

    def get_top_performing_posts(self, posts: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing posts by engagement"""
        if not posts:
            return []
        
        sorted_posts = sorted(posts, key=lambda x: x.get('engagement', 0), reverse=True)
        return sorted_posts[:limit]

    def get_low_performing_posts(self, posts: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get low performing posts by engagement"""
        if not posts:
            return []
        
        sorted_posts = sorted(posts, key=lambda x: x.get('engagement', 0))
        return sorted_posts[:limit]

    def filter_posts_by_time(self, posts: List[Dict[str, Any]], time_filter: TimeFilter) -> List[Dict[str, Any]]:
        """Filter posts by time range"""
        if not posts:
            return []
            
        filtered_posts = []
        
        for post in posts:
            post_time = post.get('timestamp')
            
            if not post_time:
                print(f"DEBUG: Post {post.get('id', 'unknown')} has no timestamp, skipping")
                continue
                
            # Handle different timestamp formats
            if isinstance(post_time, str):
                try:
                    # Try parsing ISO format first
                    if 'T' in post_time:
                        post_time = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
                    else:
                        # Try parsing date-only format
                        post_time = datetime.strptime(post_time, '%Y-%m-%d')
                except Exception as e:
                    print(f"DEBUG: Failed to parse timestamp '{post_time}' for post {post.get('id', 'unknown')}: {e}")
                    continue
            elif not isinstance(post_time, datetime):
                print(f"DEBUG: Invalid timestamp type for post {post.get('id', 'unknown')}: {type(post_time)}")
                continue
            
            # Check if post is within the time filter range
            if time_filter.start_date <= post_time <= time_filter.end_date:
                filtered_posts.append(post)
                print(f"DEBUG: Post {post.get('id', 'unknown')} included (timestamp: {post_time})")
            else:
                print(f"DEBUG: Post {post.get('id', 'unknown')} excluded (timestamp: {post_time}, range: {time_filter.start_date} to {time_filter.end_date})")
        
        print(f"DEBUG: Filtered {len(posts)} posts down to {len(filtered_posts)}")
        return filtered_posts

    def export_to_csv(self, brands_data: Dict[str, Any], analysis_id: str, 
                     time_filter: Optional[TimeFilter] = None) -> str:
        """Export analysis results to CSV"""
        all_posts = []
        
        for brand_name, brand_data in brands_data.items():
            # Collect all posts from both platforms
            instagram_posts = brand_data.get("instagram", {}).get("posts", [])
            facebook_posts = brand_data.get("facebook", {}).get("posts", [])
            
            brand_posts = instagram_posts + facebook_posts
            
            # Apply time filter if provided
            if time_filter:
                brand_posts = self.filter_posts_by_time(brand_posts, time_filter)
            
            # Add brand information to each post
            for post in brand_posts:
                post_data = post.copy()
                post_data['brand'] = brand_name
                
                # Ensure timestamp is string for CSV
                if isinstance(post_data.get('timestamp'), datetime):
                    post_data['timestamp'] = post_data['timestamp'].isoformat()
                
                # Convert lists to comma-separated strings
                if isinstance(post_data.get('hashtags'), list):
                    post_data['hashtags'] = ', '.join(post_data['hashtags'])
                
                if isinstance(post_data.get('thumbnails'), list):
                    post_data['thumbnails'] = ', '.join(post_data['thumbnails'])
                
                all_posts.append(post_data)
        
        # Convert to DataFrame
        if all_posts:
            df = pd.DataFrame(all_posts)
            # Select relevant columns for CSV
            columns = ['brand', 'platform', 'model', 'timestamp', 'engagement', 
                      'likes', 'comments', 'shares', 'reactions', 'url', 'caption', 
                      'text', 'hashtags', 'thumbnail', 'classification_reason', 
                      'classification_confidence']
            df = df.reindex(columns=[col for col in columns if col in df.columns])
        else:
            # Create empty DataFrame with expected columns
            columns = ['brand', 'platform', 'model', 'timestamp', 'engagement', 
                      'likes', 'comments', 'shares', 'reactions', 'url', 'caption', 'text']
            df = pd.DataFrame(columns=columns)
        
        # Save to CSV
        csv_path = f"results/analysis_{analysis_id}_results.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        return csv_path