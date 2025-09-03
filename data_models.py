from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class BrandConfig(BaseModel):
    instagram_url: str
    facebook_url: str
    keywords: List[str]

class TimeFilter(BaseModel):
    start_date: datetime
    end_date: datetime

class SocialMediaPost(BaseModel):
    id: str
    platform: str
    url: str
    text: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    likes: int = 0
    comments: int = 0
    shares: int = 0
    reactions: int = 0
    engagement: int = 0
    timestamp: datetime
    thumbnail: Optional[str] = None
    thumbnails: List[str] = []
    media_type: Optional[str] = None
    model: Optional[str] = None
    brand: Optional[str] = None
    classification_reason: Optional[str] = None
    classification_confidence: Optional[int] = None

class ProfileData(BaseModel):
    username: str
    followers: int
    following: Optional[int] = 0
    posts_count: Optional[int] = 0
    platform: str

class EngagementMetrics(BaseModel):
    total_posts: int
    total_engagement: int
    average_engagement: float
    model_breakdown: Dict[str, Dict[str, Any]]

class AnalysisResult(BaseModel):
    analysis_id: str
    status: str
    progress: int
    message: str
    brands_data: Dict[str, Any]
    universal_filter: Dict[str, Any]
    reference_images: Optional[Dict[str, Dict[str, List[str]]]] = None

class ClassificationRequest(BaseModel):
    posts: List[Dict[str, Any]]
    keywords: List[str]
    platform: str
    brand_name: str
    reference_images: Optional[Dict[str, List[str]]] = None