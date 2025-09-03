import os
from typing import Dict, List
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

class Calculator:
    def __init__(self, apify_token: str):
        """Initialize Calculator with Apify token"""
        if not apify_token:
            raise ValueError("Apify token is missing. Please set APIFY_TOKEN in the .env file.")
        self.apify_client = ApifyClient(apify_token)

    def get_instagram_metrics(self, instagram_url: str, keywords: List[str]) -> str:
        """Get Instagram metrics using Apify, filtering posts by multiple keywords in caption or hashtags"""
        print(f"\nFetching Instagram metrics for: {instagram_url} with keywords: {', '.join(keywords)}")
        
        try:
            # Profile details
            run_input = {"usernames": [instagram_url]}
            run = self.apify_client.actor("dSCLg0C3YEZ83HzYX").call(run_input=run_input)
            if not run:
                raise RuntimeError("Apify actor call failed for Instagram profile.")
            
            followers = 0
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                followers = item.get('followersCount', 0)
                break  # We only need the first result for followers count
                
            print(f"Found {followers} followers")
            
            # Posts engagement with keyword filtering
            run_input = {
                "directUrls": [instagram_url],
                "resultsType": "posts",
                "resultsLimit": 10,
                "onlyPostsNewerThan": "1 month"
            }
            run = self.apify_client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
            if not run:
                raise RuntimeError("Apify actor call failed for Instagram posts.")
            
            total_engagement = 0
            post_count = 0
            post_data = []
            
            print("Processing Instagram posts...")
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                caption = item.get('caption', '').lower()
                hashtags = [tag.lower() for tag in item.get('hashtags', [])]
                hashtags_str = ' '.join(hashtags)
                
                # Check if any keyword is in caption or hashtags
                if all(keyword.lower() in caption or keyword.lower() in hashtags_str for keyword in keywords):
                    post_count += 1
                    engagement = item.get('commentsCount', 0) + item.get('likesCount', 0)
                    total_engagement += engagement
                    
                    # Format time to show only date (YYYY-MM-DD)
                    time_stamp = item.get('timestamp', '')
                    formatted_date = ''
                    if time_stamp:
                        try:
                            formatted_date = time_stamp.split('T')[0]
                        except:
                            formatted_date = time_stamp
                    
                    post_data.append({
                        'Time': formatted_date,
                        'URL': item.get('url', ''),
                        'Text': item.get('caption', ''),
                        'Hashtags': ', '.join(item.get('hashtags', [])),
                        'Likes': item.get('likesCount', 0),
                        'Comments': item.get('commentsCount', 0),
                        'Engagement': engagement
                    })
                    print(f"Found matching post with {engagement} engagement")

            # Generate CSV filename based on keywords
            keyword_str = '_'.join(keyword.lower().replace(' ', '_') for keyword in keywords)
            csv_filename = f"instagram_{keyword_str}_posts.csv"
            
            if post_data:
                df = pd.DataFrame(post_data)
                os.makedirs(os.path.dirname(csv_filename) if os.path.dirname(csv_filename) else '.', exist_ok=True)
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"\nFiltered Instagram posts saved to: {csv_filename}")
                print(f"Total posts found: {post_count}")
                print(f"Total engagement: {total_engagement}")
            else:
                df = pd.DataFrame(columns=['Time', 'URL', 'Text', 'Hashtags', 'Likes', 'Comments', 'Engagement'])
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"\nNo matching Instagram posts found. Empty CSV created: {csv_filename}")
            
            return csv_filename
            
        except Exception as e:
            print(f"Error fetching Instagram metrics: {e}")
            keyword_str = '_'.join(keyword.lower().replace(' ', '_') for keyword in keywords)
            csv_filename = f"instagram_{keyword_str}_posts.csv"
            df = pd.DataFrame(columns=['Time', 'URL', 'Text', 'Hashtags', 'Likes', 'Comments', 'Engagement'])
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Error occurred. Empty CSV created: {csv_filename}")
            return csv_filename

    def get_facebook_metrics(self, facebook_url: str, keywords: List[str]) -> str:
        """Get Facebook metrics using Apify, filtering posts by multiple keywords in text"""
        print(f"\nFetching Facebook metrics for: {facebook_url} with keywords: {', '.join(keywords)}")
        
        try:
            # Profile details
            run_input = {"startUrls": [{"url": facebook_url}]}
            run = self.apify_client.actor("4Hv5RhChiaDk6iwad").call(run_input=run_input)
            if not run:
                raise RuntimeError("Apify actor call failed for Facebook profile.")
            
            followers = 0
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                followers = item.get('followers', 0)
                break
                
            print(f"Found {followers} followers")
            
            # Posts engagement with keyword filtering
            run_input = {
                "onlyPostsNewerThan": "1 month",
                "startUrls": [{"url": facebook_url}],
                "resultsLimit": 10
            }
            run = self.apify_client.actor("KoJrdxJCTtpon81KY").call(run_input=run_input)
            if not run:
                raise RuntimeError("Apify actor call failed for Facebook posts.")
            
            total_engagement = 0
            post_count = 0
            posts_data = []
            
            print("Processing Facebook posts...")
            total_posts_processed = 0
            
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                total_posts_processed += 1
                post_text = item.get('text', '').lower() if item.get('text') else ''
                
                print(f"\nPost #{total_posts_processed}:")
                print(f"  Text preview: {post_text[:100]}...")
                print(f"  Looking for keywords: {', '.join(keywords)}")
                print(f"  Any keyword in text: {any(keyword.lower() in post_text for keyword in keywords)}")
                
                if all(keyword.lower() in post_text for keyword in keywords):
                    post_count += 1
                    engagement = (
                        item.get('likes', 0) +
                        item.get('topReactionsCount', 0) +
                        item.get('shares', 0) +
                        item.get('comments', 0)
                    )
                    total_engagement += engagement
                    
                    time_stamp = item.get('time', '')
                    formatted_date = ''
                    if time_stamp:
                        try:
                            formatted_date = time_stamp.split('T')[0]
                        except:
                            formatted_date = time_stamp
                    
                    posts_data.append({
                        'Date': formatted_date,
                        'URL': item.get('topLevelUrl', ''),
                        'Text': item.get('text', ''),
                        'Likes': item.get('likes', 0),
                        'Reactions': item.get('topReactionsCount', 0),
                        'Shares': item.get('shares', 0),
                        'Comments': item.get('comments', 0),
                        'Engagement': engagement
                    })
                    print(f"  ✓ MATCH FOUND! Post with {engagement} engagement")
                else:
                    print(f"  ✗ No match found")
                    
            print(f"\nTotal posts processed from Apify: {total_posts_processed}")
            print(f"Posts matching keywords '{', '.join(keywords)}': {post_count}")
            
            keyword_str = '_'.join(keyword.lower().replace(' ', '_') for keyword in keywords)
            csv_filename = f"facebook_{keyword_str}_posts.csv"
            
            if posts_data:
                df = pd.DataFrame(posts_data)
                os.makedirs(os.path.dirname(csv_filename) if os.path.dirname(csv_filename) else '.', exist_ok=True)
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"\nFiltered Facebook posts saved to: {csv_filename}")
                print(f"Total posts found: {post_count}")
                print(f"Total engagement: {total_engagement}")
            else:
                df = pd.DataFrame(columns=['Date', 'URL', 'Text', 'Likes', 'Reactions', 'Shares', 'Comments', 'Engagement'])
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"\nNo matching Facebook posts found. Empty CSV created: {csv_filename}")
            
            return csv_filename
            
        except Exception as e:
            print(f"Error fetching Facebook metrics: {e}")
            keyword_str = '_'.join(keyword.lower().replace(' ', '_') for keyword in keywords)
            csv_filename = f"facebook_{keyword_str}_posts.csv"
            df = pd.DataFrame(columns=['Date', 'URL', 'Text', 'Likes', 'Reactions', 'Shares', 'Comments', 'Engagement'])
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Error occurred. Empty CSV created: {csv_filename}")
            return csv_filename

def main():
    load_dotenv()
    apify_token = os.getenv('APIFY_TOKEN')
    if not apify_token:
        print("Error: APIFY_TOKEN not found in .env file.")
        return

    try:
        calculator = Calculator(apify_token)
    except ValueError as e:
        print(e)
        return

    brands = {
        "Deepal": {
            "instagram_url": "https://www.instagram.com/byd_srilanka/",
            "facebook_url": "https://www.facebook.com/profile.php?id=61553703684597",
            "keywords": ["SEALION 6", "Nissan"]  # Multiple keywords
        }
    }

    for brand, data in brands.items():
        print(f"\n{'='*50}")
        print(f"Processing metrics for {brand}")
        print(f"{'='*50}")
        
        instagram_csv = calculator.get_instagram_metrics(data["instagram_url"], data["keywords"])
        facebook_csv = calculator.get_facebook_metrics(data["facebook_url"], data["keywords"])
        
        print(f"\nCompleted processing for {brand}")
        print(f"Instagram CSV: {instagram_csv}")
        print(f"Facebook CSV: {facebook_csv}")
        
        if os.path.exists(instagram_csv):
            print(f"✓ Instagram CSV file created successfully")
        else:
            print(f"✗ Instagram CSV file was not created")
            
        if os.path.exists(facebook_csv):
            print(f"✓ Facebook CSV file created successfully")
        else:
            print(f"✗ Facebook CSV file was not created")

if __name__ == "__main__":
    main()