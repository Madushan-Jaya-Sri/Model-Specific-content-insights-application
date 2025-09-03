import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "social_media_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def _serialize_datetime_objects(self, obj):
        """Recursively convert datetime objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'model_dump'):  # Pydantic model
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):  # Regular class with attributes
            return {key: self._serialize_datetime_objects(value) for key, value in obj.__dict__.items()}
        else:
            return obj

    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Analysis results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        analysis_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        message TEXT,
                        brands_data TEXT,  -- JSON string
                        universal_filter TEXT,  -- JSON string
                        reference_images TEXT,  -- JSON string
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Brand configurations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id TEXT,
                        brand_name TEXT,
                        instagram_url TEXT,
                        facebook_url TEXT,
                        keywords TEXT,  -- JSON string
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES analysis_results (analysis_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_analysis_result(self, analysis_id: str, data: Dict[str, Any]):
        """Save or update analysis result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert datetime objects to strings
                data_copy = self._serialize_datetime_objects(data)
                
                # Convert complex data to JSON strings
                brands_data_json = json.dumps(data_copy.get('brands_data', {}))
                universal_filter_json = json.dumps(data_copy.get('universal_filter', {}))
                reference_images_json = json.dumps(data_copy.get('reference_images', {}))
                
                # Insert or update
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis_results 
                    (analysis_id, status, progress, message, brands_data, 
                     universal_filter, reference_images, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    analysis_id,
                    data.get('status', 'unknown'),
                    data.get('progress', 0),
                    data.get('message', ''),
                    brands_data_json,
                    universal_filter_json,
                    reference_images_json
                ))
                
                conn.commit()
                logger.info(f"Analysis {analysis_id} saved to database")
                
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            raise
    
    def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT status, progress, message, brands_data, 
                           universal_filter, reference_images
                    FROM analysis_results 
                    WHERE analysis_id = ?
                ''', (analysis_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'analysis_id': analysis_id,
                        'status': result[0],
                        'progress': result[1],
                        'message': result[2],
                        'brands_data': json.loads(result[3]) if result[3] else {},
                        'universal_filter': json.loads(result[4]) if result[4] else {},
                        'reference_images': json.loads(result[5]) if result[5] else {}
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving analysis result: {e}")
            return None
    
    def list_analysis_results(self, limit: int = 10) -> list:
        """Get list of recent analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT analysis_id, status, progress, message, updated_at
                    FROM analysis_results 
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return [
                    {
                        'analysis_id': row[0],
                        'status': row[1],
                        'progress': row[2],
                        'message': row[3],
                        'updated_at': row[4]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error listing analysis results: {e}")
            return []
    
    def save_brand_configs(self, analysis_id: str, brands_config: Dict[str, Any]):
        """Save brand configurations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for brand_name, config in brands_config.items():
                    # Handle both BrandConfig objects and dictionaries
                    if hasattr(config, 'instagram_url'):
                        # It's a BrandConfig object
                        instagram_url = config.instagram_url
                        facebook_url = config.facebook_url
                        keywords = config.keywords
                    else:
                        # It's a dictionary
                        instagram_url = config.get('instagram_url', '')
                        facebook_url = config.get('facebook_url', '')
                        keywords = config.get('keywords', [])
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO brand_configs 
                        (analysis_id, brand_name, instagram_url, facebook_url, keywords)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        analysis_id,
                        brand_name,
                        instagram_url,
                        facebook_url,
                        json.dumps(keywords)
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving brand configs: {e}")
            raise
    
    def get_brand_configs(self, analysis_id: str) -> Dict[str, Any]:
        """Get brand configurations for an analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT brand_name, instagram_url, facebook_url, keywords
                    FROM brand_configs 
                    WHERE analysis_id = ?
                ''', (analysis_id,))
                
                results = cursor.fetchall()
                brand_configs = {}
                
                for row in results:
                    brand_configs[row[0]] = {
                        'instagram_url': row[1],
                        'facebook_url': row[2],
                        'keywords': json.loads(row[3]) if row[3] else []
                    }
                
                return brand_configs
                
        except Exception as e:
            logger.error(f"Error retrieving brand configs: {e}")
            return {}
    
    def delete_analysis_result(self, analysis_id: str) -> bool:
        """Delete analysis result and associated data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete from all related tables
                cursor.execute('DELETE FROM brand_configs WHERE analysis_id = ?', (analysis_id,))
                cursor.execute('DELETE FROM analysis_results WHERE analysis_id = ?', (analysis_id,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted analysis {analysis_id}, affected rows: {deleted_count}")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False
    
    def cleanup_old_results(self, days_old: int = 7):
        """Clean up analysis results older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM analysis_results 
                    WHERE updated_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old analysis results")
                
        except Exception as e:
            logger.error(f"Error cleaning up old results: {e}")