'''
Complete YouTube Client with Analytics and Management Capabilities.

This client provides full access to YouTube Data API and YouTube Analytics API
for comprehensive channel management and analytics.
'''

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API scopes for full access
FULL_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly'
]

class YouTubeClientFull:
    '''Complete YouTube client with analytics and management capabilities.'''

    def __init__(self, configs_dir: Path = None):
        """Initialize the YouTube client."""
        self.configs_dir = configs_dir or Path(__file__).parent.parent / "configs"
        self.scopes = FULL_SCOPES
        self.credentials = None
        self.youtube = None
        self.youtube_analytics = None
        self.channel_id = None
        
        logger.info(f"Initializing full YouTube client with {len(self.scopes)} scopes")

    def authenticate(self) -> bool:
        """
        Authenticate using existing credentials or start new OAuth flow.
        """
        try:
            # Check for existing credentials first
            token_file = self.configs_dir / "token.pickle"
            
            if token_file.exists():
                logger.info("Loading existing credentials")
                try:
                    with open(token_file, 'rb') as token:
                        self.credentials = pickle.load(token)
                        
                    # Check if credentials are valid
                    if self.credentials and self.credentials.valid:
                        logger.info("Existing credentials are valid")
                        return self._build_services()
                    
                    # Try to refresh if expired
                    if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                        logger.info("Refreshing expired credentials")
                        self.credentials.refresh(Request())
                        
                        # Save refreshed credentials
                        with open(token_file, 'wb') as token:
                            pickle.dump(self.credentials, token)
                        
                        return self._build_services()
                        
                except Exception as e:
                    logger.warning(f"Failed to load/refresh existing credentials: {e}")
                    self.credentials = None

            logger.error("No valid credentials found. Please run authentication flow first.")
            return False
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _build_services(self) -> bool:
        """Build YouTube API services."""
        try:
            logger.info("Building YouTube API services")
            
            # Build YouTube Data API service
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            logger.info("YouTube Data API service built successfully")
            
            # Build YouTube Analytics API service
            try:
                self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=self.credentials)
                logger.info("YouTube Analytics API service built successfully")
            except Exception as e:
                logger.warning(f"Failed to build YouTube Analytics service: {e}")
                self.youtube_analytics = None
            
            # Get channel ID
            self._get_channel_id()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build services: {e}")
            return False

    def _get_channel_id(self):
        """Get the channel ID for the authenticated user."""
        try:
            request = self.youtube.channels().list(part="id", mine=True)
            response = request.execute()
            
            if response.get('items'):
                self.channel_id = response['items'][0]['id']
                logger.info(f"Channel ID: {self.channel_id}")
            else:
                logger.warning("No channel found for authenticated user")
                
        except Exception as e:
            logger.error(f"Failed to get channel ID: {e}")

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive channel information."""
        if not self.youtube:
            logger.error("YouTube API not available")
            return None
        
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails,brandingSettings",
                mine=True
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.error("No channel found")
                return None
            
            channel = response['items'][0]
            
            channel_info = {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'custom_url': channel['snippet'].get('customUrl', ''),
                'published_at': channel['snippet']['publishedAt'],
                'thumbnail_url': channel['snippet']['thumbnails']['default']['url'],
                'subscriber_count': channel['statistics'].get('subscriberCount', '0'),
                'video_count': channel['statistics'].get('videoCount', '0'),
                'view_count': channel['statistics'].get('viewCount', '0'),
                'uploads_playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
            }
            
            # Add branding settings if available
            if 'brandingSettings' in channel:
                branding = channel['brandingSettings']
                if 'channel' in branding:
                    channel_info.update({
                        'keywords': branding['channel'].get('keywords', ''),
                        'default_language': branding['channel'].get('defaultLanguage', ''),
                        'country': branding['channel'].get('country', '')
                    })
            
            logger.info(f"Retrieved channel info for: {channel_info['title']}")
            return channel_info
            
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return None

    def get_recent_videos(self, max_results: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get recent videos from the channel."""
        if not self.youtube:
            logger.error("YouTube API not available")
            return None
        
        try:
            # Get uploads playlist ID
            channel_info = self.get_channel_info()
            if not channel_info:
                return None
            
            uploads_playlist_id = channel_info['uploads_playlist_id']
            
            # Get videos from uploads playlist
            request = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video = {
                    'video_id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                }
                videos.append(video)
            
            logger.info(f"Retrieved {len(videos)} recent videos")
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get recent videos: {e}")
            return None

    def get_video_analytics(self, video_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific video."""
        if not self.youtube_analytics or not self.channel_id:
            logger.error("YouTube Analytics API not available or no channel ID")
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get video analytics
            request = self.youtube_analytics.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date.strftime('%Y-%m-%d'),
                endDate=end_date.strftime('%Y-%m-%d'),
                metrics='views,likes,dislikes,comments,shares,estimatedMinutesWatched,averageViewDuration',
                dimensions='video',
                filters=f'video=={video_id}'
            )
            response = request.execute()
            
            if not response.get('rows'):
                logger.warning(f"No analytics data found for video {video_id}")
                return None
            
            # Parse analytics data
            headers = [col['name'] for col in response['columnHeaders']]
            data = response['rows'][0]
            
            analytics = {}
            for i, header in enumerate(headers):
                if i < len(data):
                    analytics[header] = data[i]
            
            logger.info(f"Retrieved analytics for video {video_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get video analytics: {e}")
            return None

    def get_channel_analytics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get channel analytics for the specified period."""
        if not self.youtube_analytics or not self.channel_id:
            logger.error("YouTube Analytics API not available or no channel ID")
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get channel analytics
            request = self.youtube_analytics.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date.strftime('%Y-%m-%d'),
                endDate=end_date.strftime('%Y-%m-%d'),
                metrics='views,likes,dislikes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost'
            )
            response = request.execute()
            
            if not response.get('rows'):
                logger.warning("No analytics data found for channel")
                return None
            
            # Parse analytics data
            headers = [col['name'] for col in response['columnHeaders']]
            data = response['rows'][0]
            
            analytics = {}
            for i, header in enumerate(headers):
                if i < len(data):
                    analytics[header] = data[i]
            
            # Calculate additional metrics
            if 'subscribersGained' in analytics and 'subscribersLost' in analytics:
                analytics['net_subscribers'] = analytics['subscribersGained'] - analytics['subscribersLost']
            
            logger.info(f"Retrieved channel analytics for {days} days")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get channel analytics: {e}")
            return None

    def get_revenue_analytics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get revenue analytics (requires monetization)."""
        if not self.youtube_analytics or not self.channel_id:
            logger.error("YouTube Analytics API not available or no channel ID")
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get revenue analytics
            request = self.youtube_analytics.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date.strftime('%Y-%m-%d'),
                endDate=end_date.strftime('%Y-%m-%d'),
                metrics='estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue,grossRevenue,cpm,playbackBasedCpm'
            )
            response = request.execute()
            
            if not response.get('rows'):
                logger.warning("No revenue data found (channel may not be monetized)")
                return None
            
            # Parse revenue data
            headers = [col['name'] for col in response['columnHeaders']]
            data = response['rows'][0]
            
            revenue = {}
            for i, header in enumerate(headers):
                if i < len(data):
                    revenue[header] = data[i]
            
            logger.info(f"Retrieved revenue analytics for {days} days")
            return revenue
            
        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {e}")
            return None

    def test_full_access(self) -> Dict[str, Any]:
        """Test all available functionalities."""
        results = {
            'authenticated': False,
            'youtube_data_api': False,
            'youtube_analytics_api': False,
            'channel_access': False,
            'analytics_access': False,
            'revenue_access': False,
            'errors': []
        }
        
        if not self.credentials:
            results['errors'].append("No credentials available")
            return results
        
        results['authenticated'] = True
        
        # Test YouTube Data API
        if self.youtube:
            results['youtube_data_api'] = True
            
            # Test channel access
            channel_info = self.get_channel_info()
            if channel_info:
                results['channel_access'] = True
                results['channel_info'] = channel_info
                
                # Test recent videos
                videos = self.get_recent_videos(5)
                if videos:
                    results['recent_videos'] = videos
        
        # Test YouTube Analytics API
        if self.youtube_analytics:
            results['youtube_analytics_api'] = True
            
            # Test channel analytics
            analytics = self.get_channel_analytics(7)
            if analytics:
                results['analytics_access'] = True
                results['channel_analytics'] = analytics
            
            # Test revenue analytics
            revenue = self.get_revenue_analytics(7)
            if revenue:
                results['revenue_access'] = True
                results['revenue_analytics'] = revenue
        
        return results

def main():
    """Main function for testing."""
    print("YouTube Full Client - Analytics & Management")
    print("=" * 50)
    
    configs_path = Path(__file__).parent.parent / "configs"
    client = YouTubeClientFull(configs_path)
    
    # Test authentication
    if client.authenticate():
        print("✓ Authentication successful!")
        
        # Test full access
        results = client.test_full_access()
        
        print("\nFull Access Test Results:")
        print("-" * 40)
        
        for key, value in results.items():
            if key == 'errors':
                if value:
                    print("Errors:")
                    for error in value:
                        print(f"  - {error}")
            elif key == 'channel_info':
                if value:
                    print(f"\nChannel Information:")
                    print(f"  - Title: {value['title']}")
                    print(f"  - ID: {value['id']}")
                    print(f"  - Subscribers: {value['subscriber_count']}")
                    print(f"  - Videos: {value['video_count']}")
                    print(f"  - Total Views: {value['view_count']}")
                    print(f"  - Published: {value['published_at']}")
            elif key == 'recent_videos':
                if value:
                    print(f"\nRecent Videos ({len(value)}):")
                    for i, video in enumerate(value[:3], 1):
                        print(f"  {i}. {video['title']}")
                        print(f"     Published: {video['published_at']}")
            elif key == 'channel_analytics':
                if value:
                    print(f"\nChannel Analytics (Last 7 Days):")
                    print(f"  - Views: {value.get('views', 'N/A')}")
                    print(f"  - Likes: {value.get('likes', 'N/A')}")
                    print(f"  - Comments: {value.get('comments', 'N/A')}")
                    print(f"  - Watch Time: {value.get('estimatedMinutesWatched', 'N/A')} minutes")
                    print(f"  - Subscribers Gained: {value.get('subscribersGained', 'N/A')}")
                    print(f"  - Net Subscribers: {value.get('net_subscribers', 'N/A')}")
            elif key == 'revenue_analytics':
                if value:
                    print(f"\nRevenue Analytics (Last 7 Days):")
                    print(f"  - Estimated Revenue: ${value.get('estimatedRevenue', 'N/A')}")
                    print(f"  - Ad Revenue: ${value.get('estimatedAdRevenue', 'N/A')}")
                    print(f"  - CPM: ${value.get('cpm', 'N/A')}")
            elif isinstance(value, bool):
                status = "✓" if value else "✗"
                print(f"{status} {key.replace('_', ' ').title()}: {value}")
    else:
        print("✗ Authentication failed")
        print("Please ensure you have valid credentials or run the OAuth flow first.")

if __name__ == '__main__':
    main()
