#!/usr/bin/env python3
"""
🎬 YouTube Autopilot - Unified Client
====================================
The ultimate YouTube automation client combining all authentication methods,
analytics capabilities, and error handling from 6 different implementations.

Features:
- Multiple authentication methods (OAuth, API Key, Service Account)
- Complete YouTube Data API v3 integration
- Full YouTube Analytics API support
- Advanced error handling and recovery
- Automatic fallback mechanisms
- Configuration-driven operation
- Comprehensive logging and debugging

Author: YouTube Autopilot System
Version: 2.0 (Unified)
"""

import os
import json
import pickle
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthMethod(Enum):
    """Available authentication methods"""
    OAUTH = "oauth"
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    AUTO = "auto"  # Automatically choose best method

@dataclass
class YouTubeConfig:
    """Configuration for YouTube Autopilot"""
    auth_method: AuthMethod = AuthMethod.AUTO
    credentials_path: str = "configs"
    oauth_scopes: List[str] = None
    api_key: str = None
    service_account_path: str = None
    client_secrets_path: str = None
    token_path: str = None
    
    # YouTube-specific settings from config.yaml
    default_visibility: str = "public"
    default_category: str = "27"
    default_schedule_cron: str = "0 9 * * 2,5"
    shorts_schedule_cron: str = "0 15 * * *"
    default_tags: List[str] = None
    
    def __post_init__(self):
        if self.oauth_scopes is None:
            self.oauth_scopes = [
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/yt-analytics.readonly',
                'https://www.googleapis.com/auth/yt-analytics-monetary.readonly'
            ]
        
        if self.default_tags is None:
            self.default_tags = ["history", "mystery", "documentary", "education", "archaeology"]

class YouTubeAutopilot:
    """
    Unified YouTube client with multiple authentication methods and comprehensive functionality.
    
    This class combines the best features from all previous YouTube client implementations:
    - OAuth 2.0 authentication with CSRF bypass
    - API key authentication for simple operations
    - Service account support for server applications
    - Complete analytics and reporting capabilities
    - Advanced error handling and recovery
    - Automatic fallback mechanisms
    """
    
    def __init__(self, config_path: str = "configs/config.yaml", **kwargs):
        """
        Initialize YouTube Autopilot with configuration.
        
        Args:
            config_path: Path to configuration file
            **kwargs: Override configuration parameters
        """
        self.config = self._load_config(config_path, **kwargs)
        self.youtube_service = None
        self.analytics_service = None
        self.credentials = None
        self.channel_id = None
        self.channel_info = None
        
        # Initialize services
        self._initialize_services()
        
    def _load_config(self, config_path: str, **kwargs) -> YouTubeConfig:
        """Load configuration from file and override with kwargs"""
        config_data = {}
        
        # Load from YAML file if exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                    if 'youtube' in yaml_data:
                        config_data = yaml_data['youtube']
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
        
        # Override with kwargs
        config_data.update(kwargs)
        
        # Convert auth_method string to enum
        if 'auth_method' in config_data and isinstance(config_data['auth_method'], str):
            config_data['auth_method'] = AuthMethod(config_data['auth_method'])
        
        return YouTubeConfig(**config_data)
    
    def _initialize_services(self):
        """Initialize YouTube services with the best available authentication method"""
        logger.info("Initializing YouTube Autopilot services...")
        
        if self.config.auth_method == AuthMethod.AUTO:
            # Try authentication methods in order of preference
            auth_methods = [AuthMethod.OAUTH, AuthMethod.API_KEY, AuthMethod.SERVICE_ACCOUNT]
        else:
            auth_methods = [self.config.auth_method]
        
        for method in auth_methods:
            try:
                if method == AuthMethod.OAUTH:
                    if self._initialize_oauth():
                        logger.info("Successfully initialized with OAuth authentication")
                        break
                elif method == AuthMethod.API_KEY:
                    if self._initialize_api_key():
                        logger.info("Successfully initialized with API Key authentication")
                        break
                elif method == AuthMethod.SERVICE_ACCOUNT:
                    if self._initialize_service_account():
                        logger.info("Successfully initialized with Service Account authentication")
                        break
            except Exception as e:
                logger.warning(f"Failed to initialize with {method.value}: {e}")
                continue
        
        if not self.youtube_service:
            raise Exception("Failed to initialize any authentication method")
        
        # Get channel information
        self._get_channel_info()
    
    def _initialize_oauth(self) -> bool:
        """Initialize OAuth 2.0 authentication"""
        try:
            credentials_dir = Path(self.config.credentials_path)
            client_secrets_file = credentials_dir / "client_secrets.json"
            token_file = credentials_dir / "token.pickle"
            
            if not client_secrets_file.exists():
                logger.warning("OAuth client secrets file not found")
                return False
            
            creds = None
            
            # Load existing token
            if token_file.exists():
                try:
                    with open(token_file, 'rb') as token:
                        creds = pickle.load(token)
                    logger.info("Loaded existing OAuth credentials")
                except Exception as e:
                    logger.warning(f"Could not load existing token: {e}")
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Refreshed OAuth credentials")
                    except Exception as e:
                        logger.warning(f"Could not refresh credentials: {e}")
                        creds = None
                
                if not creds:
                    # Use simplified flow to avoid CSRF issues
                    flow = Flow.from_client_secrets_file(
                        str(client_secrets_file),
                        scopes=self.config.oauth_scopes,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        include_granted_scopes='true',
                        prompt='consent'
                    )
                    
                    print(f"\nPlease visit this URL to authorize the application:")
                    print(f"{auth_url}")
                    print("\nAfter authorization, you will get a code. Enter it below:")
                    
                    code = input("Enter authorization code: ").strip()
                    
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    
                    logger.info("Obtained new OAuth credentials")
                
                # Save credentials
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Saved OAuth credentials")
            
            self.credentials = creds
            
            # Build services
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            
            try:
                self.analytics_service = build('youtubeAnalytics', 'v2', credentials=creds)
                logger.info("YouTube Analytics service initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Analytics service: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"OAuth initialization failed: {e}")
            return False
    
    def _initialize_api_key(self) -> bool:
        """Initialize API key authentication"""
        try:
            api_key = self.config.api_key
            
            if not api_key:
                # Try to load from file
                api_key_file = Path(self.config.credentials_path) / "api_key.txt"
                if api_key_file.exists():
                    api_key = api_key_file.read_text().strip()
            
            if not api_key:
                logger.warning("No API key found")
                return False
            
            # Build YouTube service with API key
            self.youtube_service = build('youtube', 'v3', developerKey=api_key)
            
            # Note: Analytics service not available with API key
            logger.info("API Key authentication initialized (limited functionality)")
            return True
            
        except Exception as e:
            logger.error(f"API Key initialization failed: {e}")
            return False
    
    def _initialize_service_account(self) -> bool:
        """Initialize Service Account authentication"""
        try:
            sa_file = self.config.service_account_path
            
            if not sa_file:
                sa_file = Path(self.config.credentials_path) / "service_account.json"
            
            if not os.path.exists(sa_file):
                logger.warning("Service account file not found")
                return False
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                sa_file, scopes=self.config.oauth_scopes
            )
            
            self.credentials = credentials
            
            # Build services
            self.youtube_service = build('youtube', 'v3', credentials=credentials)
            
            try:
                self.analytics_service = build('youtubeAnalytics', 'v2', credentials=credentials)
                logger.info("YouTube Analytics service initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Analytics service: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Service Account initialization failed: {e}")
            return False
    
    def _get_channel_info(self):
        """Get channel information and set channel_id"""
        try:
            if not self.youtube_service:
                return
            
            # Get channel info
            request = self.youtube_service.channels().list(
                part='snippet,statistics,contentDetails',
                mine=True
            )
            
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                self.channel_id = channel['id']
                self.channel_info = channel
                logger.info(f"Connected to channel: {channel['snippet']['title']}")
            else:
                logger.warning("No channel found for authenticated user")
                
        except Exception as e:
            logger.error(f"Could not get channel info: {e}")
    
    # === CORE FUNCTIONALITY METHODS ===
    
    def test_connection(self) -> Dict[str, Any]:
        """Test all available connections and return status"""
        results = {
            'authenticated': bool(self.credentials or self.youtube_service),
            'youtube_api': bool(self.youtube_service),
            'analytics_api': bool(self.analytics_service),
            'channel_access': bool(self.channel_id),
            'channel_info': self.channel_info
        }
        
        # Test analytics access
        if self.analytics_service and self.channel_id:
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                request = self.analytics_service.reports().query(
                    ids=f'channel=={self.channel_id}',
                    startDate=start_date,
                    endDate=end_date,
                    metrics='views,likes,comments,shares',
                    dimensions='day'
                )
                
                response = request.execute()
                results['analytics_access'] = True
                results['sample_analytics'] = response
                
            except Exception as e:
                results['analytics_access'] = False
                results['analytics_error'] = str(e)
        
        return results
    
    def get_channel_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive channel analytics"""
        if not self.analytics_service or not self.channel_id:
            logger.error("Analytics service or channel ID not available")
            return {}
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Basic metrics
            basic_request = self.analytics_service.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics='views,likes,dislikes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration'
            )
            
            basic_response = basic_request.execute()
            
            # Demographics
            demographics_request = self.analytics_service.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics='views',
                dimensions='ageGroup,gender'
            )
            
            demographics_response = demographics_request.execute()
            
            # Geography
            geography_request = self.analytics_service.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics='views',
                dimensions='country',
                sort='-views',
                maxResults=10
            )
            
            geography_response = geography_request.execute()
            
            return {
                'period': f"{start_date} to {end_date}",
                'basic_metrics': basic_response,
                'demographics': demographics_response,
                'geography': geography_response
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {'error': str(e)}
    
    def get_video_analytics(self, video_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific video"""
        if not self.analytics_service:
            logger.error("Analytics service not available")
            return {}
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            request = self.analytics_service.reports().query(
                ids=f'channel=={self.channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics='views,likes,dislikes,comments,shares,estimatedMinutesWatched,averageViewDuration',
                filters=f'video=={video_id}'
            )
            
            response = request.execute()
            return response
            
        except Exception as e:
            logger.error(f"Failed to get video analytics: {e}")
            return {'error': str(e)}
    
    def upload_video(self, video_path: str, title: str, description: str = "", 
                    tags: List[str] = None, category_id: str = "22", 
                    privacy_status: str = "private") -> Dict[str, Any]:
        """Upload a video to YouTube"""
        if not self.youtube_service:
            logger.error("YouTube service not available")
            return {'error': 'YouTube service not available'}
        
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            logger.info(f"Video uploaded successfully: {response['id']}")
            return {
                'success': True,
                'video_id': response['id'],
                'video_url': f"https://www.youtube.com/watch?v={response['id']}",
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return {'error': str(e)}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for videos"""
        if not self.youtube_service:
            logger.error("YouTube service not available")
            return []
        
        try:
            request = self.youtube_service.search().list(
                part='snippet',
                q=query,
                type='video',
                maxResults=max_results
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            logger.error(f"Failed to search videos: {e}")
            return []
    
    def get_channel_videos(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get videos from the authenticated channel"""
        if not self.youtube_service or not self.channel_id:
            logger.error("YouTube service or channel ID not available")
            return []
        
        try:
            # Get uploads playlist ID
            channel_request = self.youtube_service.channels().list(
                part='contentDetails',
                id=self.channel_id
            )
            
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            playlist_request = self.youtube_service.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            
            playlist_response = playlist_request.execute()
            return playlist_response.get('items', [])
            
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
    
    def update_video(self, video_id: str, title: str = None, description: str = None, 
                    tags: List[str] = None) -> Dict[str, Any]:
        """Update video metadata"""
        if not self.youtube_service:
            logger.error("YouTube service not available")
            return {'error': 'YouTube service not available'}
        
        try:
            # Get current video details
            video_request = self.youtube_service.videos().list(
                part='snippet',
                id=video_id
            )
            
            video_response = video_request.execute()
            
            if not video_response['items']:
                return {'error': 'Video not found'}
            
            current_snippet = video_response['items'][0]['snippet']
            
            # Update only provided fields
            if title is not None:
                current_snippet['title'] = title
            if description is not None:
                current_snippet['description'] = description
            if tags is not None:
                current_snippet['tags'] = tags
            
            # Update video
            update_request = self.youtube_service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': current_snippet
                }
            )
            
            response = update_request.execute()
            
            logger.info(f"Video updated successfully: {video_id}")
            return {'success': True, 'response': response}
            
        except Exception as e:
            logger.error(f"Failed to update video: {e}")
            return {'error': str(e)}
    
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get comments for a video"""
        if not self.youtube_service:
            logger.error("YouTube service not available")
            return []
        
        try:
            request = self.youtube_service.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            logger.error(f"Failed to get video comments: {e}")
            return []
    
    # === UTILITY METHODS ===
    
    def get_auth_method(self) -> str:
        """Get the current authentication method being used"""
        if self.credentials:
            if hasattr(self.credentials, 'refresh_token'):
                return "OAuth 2.0"
            else:
                return "Service Account"
        else:
            return "API Key"
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the YouTube Autopilot"""
        return {
            'auth_method': self.get_auth_method(),
            'youtube_service': bool(self.youtube_service),
            'analytics_service': bool(self.analytics_service),
            'channel_id': self.channel_id,
            'channel_info': self.channel_info,
            'config': {
                'auth_method': self.config.auth_method.value,
                'credentials_path': self.config.credentials_path,
                'scopes': self.config.oauth_scopes
            }
        }

def main():
    """Test the YouTube Autopilot client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Autopilot - Unified Client')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    parser.add_argument('--analytics', type=int, default=7, help='Get analytics for N days')
    parser.add_argument('--videos', action='store_true', help='List channel videos')
    parser.add_argument('--config', default='configs/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    try:
        # Initialize YouTube Autopilot
        yt = YouTubeAutopilot(config_path=args.config)
        
        print("🎬 YouTube Autopilot - Unified Client")
        print("=" * 50)
        
        if args.test:
            print("Testing connection...")
            results = yt.test_connection()
            
            print(f"✓ Authenticated: {results['authenticated']}")
            print(f"✓ YouTube API: {results['youtube_api']}")
            print(f"✓ Analytics API: {results['analytics_api']}")
            print(f"✓ Channel Access: {results['channel_access']}")
            
            if results['channel_info']:
                info = results['channel_info']
                print(f"\nChannel Information:")
                print(f"  - Title: {info['snippet']['title']}")
                print(f"  - ID: {info['id']}")
                print(f"  - Subscribers: {info['statistics'].get('subscriberCount', 'Hidden')}")
                print(f"  - Videos: {info['statistics']['videoCount']}")
                print(f"  - Views: {info['statistics']['viewCount']}")
        
        if args.analytics:
            print(f"\nGetting analytics for last {args.analytics} days...")
            analytics = yt.get_channel_analytics(days=args.analytics)
            
            if 'basic_metrics' in analytics:
                metrics = analytics['basic_metrics']
                if 'rows' in metrics and metrics['rows']:
                    row = metrics['rows'][0]
                    print(f"  - Views: {row[0] if len(row) > 0 else 'N/A'}")
                    print(f"  - Likes: {row[1] if len(row) > 1 else 'N/A'}")
                    print(f"  - Comments: {row[3] if len(row) > 3 else 'N/A'}")
                    print(f"  - Watch Time: {row[7] if len(row) > 7 else 'N/A'} minutes")
        
        if args.videos:
            print("\nChannel Videos:")
            videos = yt.get_channel_videos(max_results=10)
            
            for i, video in enumerate(videos[:5], 1):
                snippet = video['snippet']
                print(f"  {i}. {snippet['title']}")
                print(f"     Published: {snippet['publishedAt'][:10]}")
        
        print(f"\nAuthentication Method: {yt.get_auth_method()}")
        print("YouTube Autopilot ready for automation! 🚀")
        
    except Exception as e:
        logger.error(f"Failed to initialize YouTube Autopilot: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
