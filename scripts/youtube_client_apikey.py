'''
Simple YouTube API Client using API Key for read-only operations.

This client uses API key authentication which is simpler and doesn't require OAuth.
It can be used for basic operations like getting channel info and video statistics.
'''

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
API_KEY = "AIzaSyBJVXiWgZEQs8cKGnhXKqYQs8cKGnhXKqY"  # This will be replaced with actual key

class YouTubeClientAPIKey:
    '''A simple YouTube API client using API key authentication.'''

    def __init__(self, api_key: str = None, configs_dir: Path = None):
        """
        Initialize the YouTube client with API key.
        
        Args:
            api_key: YouTube Data API key
            configs_dir: Directory containing configuration files (optional)
        """
        self.api_key = api_key or self._load_api_key(configs_dir)
        self.youtube = None
        
        if self.api_key:
            try:
                self.youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=self.api_key)
                logger.info("YouTube API client initialized successfully with API key")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube client: {e}")
        else:
            logger.error("No API key provided")

    def _load_api_key(self, configs_dir: Path) -> Optional[str]:
        """Load API key from configuration file."""
        if not configs_dir:
            return None
        
        api_key_file = configs_dir / "api_key.txt"
        if api_key_file.exists():
            try:
                with open(api_key_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read API key file: {e}")
        
        return None

    def search_videos(self, query: str, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Search for videos on YouTube."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results
            )
            response = request.execute()
            
            logger.info(f"Found {len(response.get('items', []))} videos for query: {query}")
            return response.get("items", [])
            
        except HttpError as e:
            logger.error(f"HTTP error during search: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return None

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific video."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]
            else:
                logger.warning(f"No video found with ID: {video_id}")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error getting video details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting video details: {e}")
            return None

    def get_channel_info_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel by its ID."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=channel_id
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]
            else:
                logger.warning(f"No channel found with ID: {channel_id}")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error getting channel info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting channel info: {e}")
            return None

    def get_channel_info_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel by its username."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                forUsername=username
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]
            else:
                logger.warning(f"No channel found with username: {username}")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error getting channel info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting channel info: {e}")
            return None

    def get_popular_videos(self, region_code: str = "US", max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get popular videos from a specific region."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=max_results
            )
            response = request.execute()
            
            logger.info(f"Found {len(response.get('items', []))} popular videos in {region_code}")
            return response.get("items", [])
            
        except HttpError as e:
            logger.error(f"HTTP error getting popular videos: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting popular videos: {e}")
            return None

    def test_connection(self) -> bool:
        """Test the YouTube API connection."""
        try:
            # Try to get popular videos as a simple test
            videos = self.get_popular_videos(max_results=1)
            if videos and len(videos) > 0:
                logger.info("Connection test successful - API key is working")
                return True
            else:
                logger.error("Connection test failed - no data retrieved")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

def save_api_key(configs_dir: Path, api_key: str) -> bool:
    """Save API key to configuration file."""
    api_key_file = configs_dir / "api_key.txt"
    try:
        with open(api_key_file, 'w') as f:
            f.write(api_key)
        logger.info(f"API key saved to {api_key_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save API key: {e}")
        return False

if __name__ == '__main__':
    # Example usage
    configs_path = Path(__file__).parent.parent / "configs"
    
    print("Testing YouTube API Client with API Key...")
    print("=" * 50)
    
    # Try to load API key from config file first
    client = YouTubeClientAPIKey(configs_dir=configs_path)
    
    if not client.api_key:
        print("Please save your API key to configs/api_key.txt")
        print("You can get an API key from Google Cloud Console > APIs & Services > Credentials")
        exit(1)
    
    try:
        
        if client.test_connection():
            print("✓ API key authentication successful")
            
            # Test search functionality
            print("\nTesting search functionality...")
            videos = client.search_videos("Python programming", max_results=3)
            if videos:
                print(f"✓ Found {len(videos)} videos")
                for video in videos[:2]:  # Show first 2 results
                    print(f"  - {video['snippet']['title']}")
            
            # Test getting popular videos
            print("\nTesting popular videos...")
            popular = client.get_popular_videos(max_results=3)
            if popular:
                print(f"✓ Found {len(popular)} popular videos")
                for video in popular[:2]:  # Show first 2 results
                    print(f"  - {video['snippet']['title']}")
            
        else:
            print("✗ API key authentication failed")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\nTest completed.")
