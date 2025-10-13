from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import json
import os
import uuid
import asyncio
import logging
from datetime import datetime, timedelta

from services.scraper_service import SocialMediaScraper
from services.analysis_service import AnalysisService
from services.database_service_mongo import DatabaseService
from data_models import BrandConfig, TimeFilter
from utils.image_handler import ImageHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Social Media Analytics", description="Analyze social media engagement")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("static", exist_ok=True)


# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


# Initialize services
db_service = DatabaseService()
image_handler = ImageHandler()
active_analysis = {}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html", "r") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/api/image-proxy")
async def image_proxy(url: str):
    """Proxy images to handle CORS issues"""
    try:
        image_data = await image_handler.get_proxied_image(url)
        return Response(
            content=image_data,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except Exception as e:
        logger.error(f"Image proxy error for {url}: {e}")
        placeholder = image_handler.generate_placeholder_image()
        return Response(content=placeholder, media_type="image/svg+xml")

@app.get("/api/recent-analyses")
async def get_recent_analyses():
    """Get list of recent analyses"""
    return db_service.list_analysis_results(limit=20)

@app.post("/api/analyze")
async def analyze_brands(request_data: dict):
    """Start the analysis process for given brands"""
    try:
        brands_config_dict = request_data.get('brands_config', {})
        reference_images = request_data.get('reference_images', {})
        
        # Convert dictionary to BrandConfig objects
        brands_config = {}
        for brand_name, config_data in brands_config_dict.items():
            brands_config[brand_name] = BrandConfig(
                instagram_url=config_data['instagram_url'],
                facebook_url=config_data['facebook_url'],
                keywords=config_data['keywords']
            )
        
        analysis_id = str(uuid.uuid4())
        
        # Initialize services
        scraper = SocialMediaScraper()
        analyzer = AnalysisService()
        
        # Set universal time filter (hardcoded - 3 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        universal_filter = TimeFilter(start_date=start_date, end_date=end_date)
        
        # Store initial status
        initial_data = {
            "status": "starting",
            "progress": 5,
            "message": "Initializing analysis...",
            "brands_data": {},
            "universal_filter": {
                "start_date": universal_filter.start_date.isoformat(),
                "end_date": universal_filter.end_date.isoformat()
            },
            "reference_images": reference_images
        }
        
        active_analysis[analysis_id] = initial_data
        db_service.save_analysis_result(analysis_id, initial_data)
        db_service.save_brand_configs(analysis_id, brands_config)
        
        # Start background task
        asyncio.create_task(
            process_analysis(analysis_id, brands_config, scraper, analyzer, 
                           universal_filter, reference_images)
        )
        
        return {"analysis_id": analysis_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def process_analysis(analysis_id: str, brands_config: Dict[str, BrandConfig], 
                          scraper: SocialMediaScraper, analyzer: AnalysisService, 
                          universal_filter: TimeFilter, reference_images: Dict):
    """Background task to process analysis"""
    try:
        total_brands = len(brands_config)
        total_steps = total_brands * 5
        current_step = 1
        
        def update_progress(message: str, step_increment: int = 1):
            nonlocal current_step
            current_step += step_increment
            progress_percentage = min(95, max(5, int((current_step / total_steps) * 90) + 5))
            
            progress_data = {
                "status": "processing",
                "progress": progress_percentage,
                "message": message,
                "brands_data": active_analysis[analysis_id].get("brands_data", {}),
                "universal_filter": active_analysis[analysis_id].get("universal_filter", {}),
                "reference_images": reference_images
            }
            
            active_analysis[analysis_id].update(progress_data)
            logger.info(f"Progress updated: {progress_percentage}% - {message}")
            
            # IMPORTANT: Force immediate database save (blocking for reliability)
            try:
                db_service.save_analysis_result(analysis_id, active_analysis[analysis_id])
            except Exception as e:
                logger.error(f"Failed to save progress: {e}")
            
            return progress_percentage

        await asyncio.sleep(0.5)
        update_progress("Starting to scrape social media data...", 0)
        
        for brand_name, brand_config in brands_config.items():
            brand_reference_images = reference_images.get(brand_name, {})
            logger.info(f"Processing {brand_name} with reference images: {list(brand_reference_images.keys())}")
            
            # Step 1: Scrape Instagram data
            update_progress(f"Scraping Instagram data for {brand_name}...")
            instagram_posts = await scraper.scrape_instagram_posts(
                brand_config.instagram_url, universal_filter
            )
            instagram_profile = await scraper.scrape_instagram_profile(brand_config.instagram_url)
            logger.info(f"Scraped {len(instagram_posts)} Instagram posts for {brand_name}")
            
            # Step 2: Scrape Facebook data
            update_progress(f"Scraping Facebook data for {brand_name}...")
            facebook_posts = await scraper.scrape_facebook_posts(
                brand_config.facebook_url, universal_filter
            )
            facebook_profile = await scraper.scrape_facebook_profile(brand_config.facebook_url)
            logger.info(f"Scraped {len(facebook_posts)} Facebook posts for {brand_name}")
            
            # Step 3: Classify Instagram posts
            update_progress(f"Analyzing Instagram posts for {brand_name}...")
            classified_instagram = await analyzer.classify_posts_with_vision(
                instagram_posts, brand_config.keywords, "instagram", brand_name, brand_reference_images
            )
            logger.info(f"Classified {len(classified_instagram)} Instagram posts for {brand_name}")
            
            # Step 4: Classify Facebook posts
            update_progress(f"Analyzing Facebook posts for {brand_name}...")
            classified_facebook = await analyzer.classify_posts_with_vision(
                facebook_posts, brand_config.keywords, "facebook", brand_name, brand_reference_images
            )
            logger.info(f"Classified {len(classified_facebook)} Facebook posts for {brand_name}")
            
            # Step 5: Calculate metrics and store results
            update_progress(f"Calculating engagement metrics for {brand_name}...")
            
            all_posts = classified_instagram + classified_facebook
            engagement_metrics = analyzer.calculate_engagement_metrics(all_posts, brand_config.keywords)
            
            # Store brand results
            active_analysis[analysis_id]["brands_data"][brand_name] = {
                "instagram": {
                    "profile": instagram_profile.model_dump() if hasattr(instagram_profile, 'model_dump') else instagram_profile.__dict__,
                    "posts": classified_instagram,
                    "metrics": engagement_metrics.get("instagram", {})
                },
                "facebook": {
                    "profile": facebook_profile.model_dump() if hasattr(facebook_profile, 'model_dump') else facebook_profile.__dict__,
                    "posts": classified_facebook,
                    "metrics": engagement_metrics.get("facebook", {})
                },
                "overall_metrics": engagement_metrics.get("overall", {}),
                "top_posts": analyzer.get_top_performing_posts(all_posts, 5),
                "low_posts": analyzer.get_low_performing_posts(all_posts, 5),
                "keywords": brand_config.keywords
            }
        
        # Set final progress
        final_data = {
            "status": "completed",
            "progress": 100,
            "message": "Analysis completed successfully!",
            "brands_data": active_analysis[analysis_id]["brands_data"],
            "universal_filter": active_analysis[analysis_id]["universal_filter"],
            "reference_images": reference_images
        }
        active_analysis[analysis_id].update(final_data)
        
        # Final database save
        await save_progress_async(analysis_id, active_analysis[analysis_id])
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error during analysis {analysis_id}: {e}")
        error_data = {
            "status": "error",
            "progress": current_step if 'current_step' in locals() else 0,
            "message": f"Error during analysis: {str(e)}",
            "brands_data": active_analysis[analysis_id].get("brands_data", {}),
            "universal_filter": active_analysis[analysis_id].get("universal_filter", {}),
            "reference_images": reference_images
        }
        active_analysis[analysis_id].update(error_data)
        
        try:
            db_service.save_analysis_result(analysis_id, active_analysis[analysis_id])
        except Exception as db_error:
            logger.error(f"Error saving error state to database: {db_error}")

async def save_progress_async(analysis_id: str, data: dict):
    """Save progress to database asynchronously"""
    try:
        # Use run_in_executor to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, db_service.save_analysis_result, analysis_id, data)
    except Exception as e:
        logger.error(f"Error saving progress to database: {e}")

@app.post("/api/upload-reference-images")
async def upload_reference_images(
    files: List[UploadFile] = File(...),
    brand: str = Form(...),
    model: str = Form(...),
    analysis_id: str = Form(...)
):
    """Upload reference images for a specific model"""
    try:
        ref_dir = f"uploads/reference/{analysis_id}/{brand}/{model}"
        os.makedirs(ref_dir, exist_ok=True)
        
        image_paths = []
        for i, file in enumerate(files[:3]):  # Limit to 3 images
            if file.content_type.startswith('image/'):
                file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
                file_path = f"{ref_dir}/ref_{i+1}.{file_extension}"
                
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                image_paths.append(file_path)
        
        return {
            "message": f"Uploaded {len(image_paths)} reference images for {brand} - {model}",
            "paths": image_paths
        }
        
    except Exception as e:
        logger.error(f"Error uploading reference images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get the current status of an analysis"""
    # First check active memory
    if analysis_id in active_analysis:
        result = active_analysis[analysis_id]
        return result
    
    # Then check database
    result = db_service.get_analysis_result(analysis_id)
    if result:
        return result
    
    raise HTTPException(status_code=404, detail="Analysis not found")

@app.post("/api/filter-results/{analysis_id}")
async def filter_results_by_time(analysis_id: str, time_filter: TimeFilter):
    """Filter analysis results by time range"""
    try:
        print(f"DEBUG: Filter request for analysis {analysis_id}")
        print(f"DEBUG: Time filter - start: {time_filter.start_date}, end: {time_filter.end_date}")
        
        analysis_data = active_analysis.get(analysis_id) or db_service.get_analysis_result(analysis_id)
        if not analysis_data:
            print(f"DEBUG: Analysis {analysis_id} not found")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        print(f"DEBUG: Found analysis data with {len(analysis_data.get('brands_data', {}))} brands")
        
        analyzer = AnalysisService()
        filtered_results = {}
        
        # Filter results for each brand
        for brand_name, brand_data in analysis_data["brands_data"].items():
            print(f"DEBUG: Processing brand {brand_name}")
            
            original_keywords = brand_data.get("keywords", [])
            print(f"DEBUG: Original keywords for {brand_name}: {original_keywords}")
            
            # Filter posts
            original_instagram_posts = brand_data.get("instagram", {}).get("posts", [])
            original_facebook_posts = brand_data.get("facebook", {}).get("posts", [])
            
            print(f"DEBUG: Original posts - Instagram: {len(original_instagram_posts)}, Facebook: {len(original_facebook_posts)}")
            
            filtered_instagram = analyzer.filter_posts_by_time(original_instagram_posts, time_filter)
            filtered_facebook = analyzer.filter_posts_by_time(original_facebook_posts, time_filter)
            
            print(f"DEBUG: Filtered posts - Instagram: {len(filtered_instagram)}, Facebook: {len(filtered_facebook)}")
            
            # Recalculate metrics
            all_filtered_posts = filtered_instagram + filtered_facebook
            engagement_metrics = analyzer.calculate_engagement_metrics(all_filtered_posts, original_keywords)
            
            print(f"DEBUG: Recalculated metrics: {engagement_metrics}")
            
            filtered_results[brand_name] = {
                "instagram": {
                    "profile": brand_data.get("instagram", {}).get("profile", {}),
                    "posts": filtered_instagram,
                    "metrics": engagement_metrics.get("instagram", {})
                },
                "facebook": {
                    "profile": brand_data.get("facebook", {}).get("profile", {}),
                    "posts": filtered_facebook,
                    "metrics": engagement_metrics.get("facebook", {})
                },
                "overall_metrics": engagement_metrics.get("overall", {}),
                "top_posts": analyzer.get_top_performing_posts(all_filtered_posts, 5),
                "low_posts": analyzer.get_low_performing_posts(all_filtered_posts, 5),
                "keywords": original_keywords
            }
        
        print(f"DEBUG: Returning filtered results for {len(filtered_results)} brands")
        
        return {
            "filtered_results": filtered_results,
            "time_filter": {
                "start_date": time_filter.start_date.isoformat(),
                "end_date": time_filter.end_date.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Error in filter_results_by_time: {e}")
        raise HTTPException(status_code=500, detail=f"Filter failed: {str(e)}")

@app.get("/api/download/{analysis_id}")
async def download_results(analysis_id: str, time_filter: Optional[str] = None):
    """Download analysis results as CSV"""
    analysis_data = active_analysis.get(analysis_id) or db_service.get_analysis_result(analysis_id)
    if not analysis_data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analyzer = AnalysisService()
    
    # Parse time filter if provided
    filter_obj = None
    if time_filter:
        try:
            filter_data = json.loads(time_filter)
            filter_obj = TimeFilter(
                start_date=datetime.fromisoformat(filter_data['start_date'].replace('Z', '+00:00')),
                end_date=datetime.fromisoformat(filter_data['end_date'].replace('Z', '+00:00'))
            )
        except Exception as e:
            logger.error(f"Error parsing time filter: {e}")
    
    try:
        csv_path = analyzer.export_to_csv(
            analysis_data["brands_data"], 
            analysis_id, 
            filter_obj
        )
        
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=500, detail="Failed to generate CSV file")
        
        return FileResponse(
            path=csv_path,
            media_type='application/octet-stream',
            filename=f"social_media_analysis_{analysis_id[:8]}.csv",
            headers={"Content-Disposition": f"attachment; filename=social_media_analysis_{analysis_id[:8]}.csv"}
        )
    
    except Exception as e:
        logger.error(f"Error generating download: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis and its associated data"""
    try:
        # Validate analysis_id
        if not analysis_id or analysis_id == "undefined" or analysis_id == "null":
            logger.warning(f"Invalid analysis ID received for deletion: {analysis_id}")
            raise HTTPException(status_code=400, detail="Invalid analysis ID")
        
        # Remove from active memory
        if analysis_id in active_analysis:
            del active_analysis[analysis_id]
        
        # Delete from database
        success = db_service.delete_analysis_result(analysis_id)
        
        if success:
            # Clean up files
            try:
                import shutil
                ref_dir = f"uploads/reference/{analysis_id}"
                if os.path.exists(ref_dir):
                    shutil.rmtree(ref_dir)
                
                csv_path = f"results/analysis_{analysis_id}_results.csv"
                if os.path.exists(csv_path):
                    os.remove(csv_path)
            except Exception as e:
                logger.warning(f"Error cleaning up files for {analysis_id}: {e}")
            
            return {"message": "Analysis deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Analysis not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
    

@app.get("/api/download/{analysis_id}")
async def download_results(analysis_id: str, time_filter: Optional[str] = None):
    """Download analysis results as CSV"""
    try:
        logger.info(f"Download request for analysis: {analysis_id}")
        
        # Get analysis data
        analysis_data = active_analysis.get(analysis_id) or db_service.get_analysis_result(analysis_id)
        if not analysis_data:
            logger.error(f"Analysis {analysis_id} not found")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if not analysis_data.get('brands_data'):
            logger.error(f"No brands data in analysis {analysis_id}")
            raise HTTPException(status_code=400, detail="No analysis data available")
        
        analyzer = AnalysisService()
        
        # Parse time filter if provided
        filter_obj = None
        if time_filter:
            try:
                filter_data = json.loads(time_filter)
                filter_obj = TimeFilter(
                    start_date=datetime.fromisoformat(filter_data['start_date'].replace('Z', '+00:00')),
                    end_date=datetime.fromisoformat(filter_data['end_date'].replace('Z', '+00:00'))
                )
                logger.info(f"Time filter applied: {filter_obj.start_date} to {filter_obj.end_date}")
            except Exception as e:
                logger.warning(f"Error parsing time filter, proceeding without it: {e}")
                filter_obj = None
        
        # Generate CSV
        try:
            csv_path = analyzer.export_to_csv(
                analysis_data["brands_data"], 
                analysis_id, 
                filter_obj
            )
            logger.info(f"CSV generated at: {csv_path}")
        except Exception as e:
            logger.error(f"Error generating CSV: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")
        
        # Verify file exists
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at: {csv_path}")
            raise HTTPException(status_code=500, detail="CSV file not found after generation")
        
        # Verify file is not empty
        file_size = os.path.getsize(csv_path)
        if file_size == 0:
            logger.error(f"Generated CSV file is empty")
            raise HTTPException(status_code=500, detail="Generated CSV file is empty")
        
        logger.info(f"CSV file ready: {csv_path} ({file_size} bytes)")
        
        filename = f"social_media_analysis_{analysis_id[:8]}.csv"
        
        return FileResponse(
            path=csv_path,
            media_type='text/csv',
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)