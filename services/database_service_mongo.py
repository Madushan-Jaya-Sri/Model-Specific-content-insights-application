import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        mongodb_url = os.getenv('MONGODB_CONNECTION_STRING')
        if not mongodb_url:
            raise ValueError("MONGODB_CONNECTION_STRING not found in .env file")
        
        self.client = MongoClient(mongodb_url)
        self.db = self.client['social_media_analytics']
        
        # Collections
        self.analysis_collection = self.db['analyses']
        self.brand_configs_collection = self.db['brand_configs']
        
        # Create indexes
        self._create_indexes()
        logger.info("MongoDB connection established successfully")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Index on analysis_id for faster lookups
            self.analysis_collection.create_index("analysis_id", unique=True)
            self.analysis_collection.create_index([("updated_at", DESCENDING)])
            
            # Index on brand configs
            self.brand_configs_collection.create_index("analysis_id")
            self.brand_configs_collection.create_index([("analysis_id", 1), ("brand_name", 1)])
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def _serialize_datetime_objects(self, obj):
        """Recursively convert datetime objects to ISO format strings"""
        if isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'model_dump'):
            return self._serialize_datetime_objects(obj.model_dump())
        elif hasattr(obj, '__dict__'):
            return self._serialize_datetime_objects(obj.__dict__)
        else:
            return obj
    
    def save_analysis_result(self, analysis_id: str, data: Dict[str, Any]):
        """Save or update analysis result in MongoDB"""
        try:
            # Serialize datetime objects
            data_copy = self._serialize_datetime_objects(data)
            
            # Prepare document for update
            update_document = {
                "analysis_id": analysis_id,
                "status": data.get('status', 'unknown'),
                "progress": data.get('progress', 0),
                "message": data.get('message', ''),
                "brands_data": data_copy.get('brands_data', {}),
                "universal_filter": data_copy.get('universal_filter', {}),
                "reference_images": data_copy.get('reference_images', {}),
                "updated_at": datetime.utcnow()
            }
            
            # Upsert (update if exists, insert if not)
            self.analysis_collection.update_one(
                {"analysis_id": analysis_id},
                {
                    "$set": update_document,
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            
            logger.info(f"Analysis {analysis_id} saved to MongoDB")
            
        except Exception as e:
            logger.error(f"Error saving analysis result to MongoDB: {e}")
            raise
    
    def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result from MongoDB"""
        try:
            document = self.analysis_collection.find_one(
                {"analysis_id": analysis_id},
                {"_id": 0}  # Exclude MongoDB's _id field
            )
            
            if document:
                # Convert datetime objects back for compatibility
                if 'updated_at' in document and isinstance(document['updated_at'], datetime):
                    document['updated_at'] = document['updated_at'].isoformat()
                if 'created_at' in document and isinstance(document['created_at'], datetime):
                    document['created_at'] = document['created_at'].isoformat()
                
                return document
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving analysis result from MongoDB: {e}")
            return None
    
    def list_analysis_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of recent analysis results from MongoDB"""
        try:
            cursor = self.analysis_collection.find(
                {},
                {
                    "_id": 0,
                    "analysis_id": 1,
                    "status": 1,
                    "progress": 1,
                    "message": 1,
                    "updated_at": 1
                }
            ).sort("updated_at", DESCENDING).limit(limit)
            
            results = []
            for doc in cursor:
                # Convert datetime to ISO string
                if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                    doc['updated_at'] = doc['updated_at'].isoformat()
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Error listing analysis results from MongoDB: {e}")
            return []
    
    def save_brand_configs(self, analysis_id: str, brands_config: Dict[str, Any]):
        """Save brand configurations to MongoDB"""
        try:
            documents = []
            
            for brand_name, config in brands_config.items():
                # Handle both BrandConfig objects and dictionaries
                if hasattr(config, 'instagram_url'):
                    instagram_url = config.instagram_url
                    facebook_url = config.facebook_url
                    keywords = config.keywords
                else:
                    instagram_url = config.get('instagram_url', '')
                    facebook_url = config.get('facebook_url', '')
                    keywords = config.get('keywords', [])
                
                document = {
                    "analysis_id": analysis_id,
                    "brand_name": brand_name,
                    "instagram_url": instagram_url,
                    "facebook_url": facebook_url,
                    "keywords": keywords,
                    "created_at": datetime.utcnow()
                }
                documents.append(document)
            
            if documents:
                # Delete existing configs for this analysis_id
                self.brand_configs_collection.delete_many({"analysis_id": analysis_id})
                # Insert new configs
                self.brand_configs_collection.insert_many(documents)
                logger.info(f"Saved {len(documents)} brand configs for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error saving brand configs to MongoDB: {e}")
            raise
    
    def get_brand_configs(self, analysis_id: str) -> Dict[str, Any]:
        """Get brand configurations for an analysis from MongoDB"""
        try:
            cursor = self.brand_configs_collection.find(
                {"analysis_id": analysis_id},
                {"_id": 0, "created_at": 0}
            )
            
            brand_configs = {}
            for doc in cursor:
                brand_name = doc.pop('analysis_id', None)  # Remove analysis_id from doc
                doc.pop('analysis_id', None)  # Ensure it's removed
                brand_configs[doc['brand_name']] = {
                    'instagram_url': doc['instagram_url'],
                    'facebook_url': doc['facebook_url'],
                    'keywords': doc['keywords']
                }
            
            return brand_configs
            
        except Exception as e:
            logger.error(f"Error retrieving brand configs from MongoDB: {e}")
            return {}
    
    def delete_analysis_result(self, analysis_id: str) -> bool:
        """Delete analysis result and associated data from MongoDB"""
        try:
            # Delete brand configs
            brand_result = self.brand_configs_collection.delete_many({"analysis_id": analysis_id})
            
            # Delete analysis
            analysis_result = self.analysis_collection.delete_one({"analysis_id": analysis_id})
            
            deleted_count = analysis_result.deleted_count
            logger.info(f"Deleted analysis {analysis_id} from MongoDB. Affected documents: {deleted_count}")
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id} from MongoDB: {e}")
            return False
    
    def cleanup_old_results(self, days_old: int = 7):
        """Clean up analysis results older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old analyses
            old_analyses = self.analysis_collection.find(
                {"updated_at": {"$lt": cutoff_date}},
                {"analysis_id": 1}
            )
            
            old_analysis_ids = [doc['analysis_id'] for doc in old_analyses]
            
            if old_analysis_ids:
                # Delete old brand configs
                self.brand_configs_collection.delete_many(
                    {"analysis_id": {"$in": old_analysis_ids}}
                )
                
                # Delete old analyses
                result = self.analysis_collection.delete_many(
                    {"updated_at": {"$lt": cutoff_date}}
                )
                
                deleted_count = result.deleted_count
                logger.info(f"Cleaned up {deleted_count} old analysis results from MongoDB")
            else:
                logger.info("No old analysis results to clean up")
                
        except Exception as e:
            logger.error(f"Error cleaning up old results from MongoDB: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")

# Import for backwards compatibility
from datetime import timedelta