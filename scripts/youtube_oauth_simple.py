'''
Simplified YouTube OAuth Client that bypasses CSRF issues.

This client uses a different approach to handle OAuth authentication
that should work around the state mismatch problem.
'''

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pickle
import webbrowser
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

class YouTubeOAuthSimple:
    '''Simplified YouTube OAuth client that bypasses CSRF issues.'''

    def __init__(self, configs_dir: Path = None):
        """Initialize the YouTube OAuth client."""
        self.configs_dir = configs_dir or Path(__file__).parent.parent / "configs"
        self.scopes = SCOPES
        self.credentials = None
        self.youtube = None
        
        logger.info(f"Initializing simple YouTube OAuth client")

    def authenticate_manual(self) -> bool:
        """
        Authenticate using manual OAuth flow without local server.
        This bypasses the CSRF state mismatch issue.
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

            # Start new OAuth flow
            client_secrets_file = self.configs_dir / "client_secrets.json"
            
            if not client_secrets_file.exists():
                logger.error(f"Client secrets file not found: {client_secrets_file}")
                return False

            logger.info("Starting manual OAuth flow")
            
            # Create flow without redirect URI issues
            flow = Flow.from_client_secrets_file(
                str(client_secrets_file),
                scopes=self.scopes
            )
            
            # Use a simple redirect URI
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            print("\n" + "="*60)
            print("MANUAL OAUTH AUTHENTICATION")
            print("="*60)
            print(f"1. Please visit this URL in your browser:")
            print(f"   {auth_url}")
            print(f"\n2. Complete the authorization process")
            print(f"3. Copy the authorization code from the final page")
            print(f"4. Paste it below")
            print("="*60)
            
            # Open browser automatically
            try:
                webbrowser.open(auth_url)
                logger.info("Opened browser automatically")
            except Exception as e:
                logger.warning(f"Could not open browser automatically: {e}")
            
            # Get authorization code from user
            auth_code = input("\nEnter the authorization code: ").strip()
            
            if not auth_code:
                logger.error("No authorization code provided")
                return False
            
            # Exchange code for credentials
            logger.info("Exchanging authorization code for credentials")
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            
            # Save credentials
            with open(token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.info("Credentials saved successfully")
            
            return self._build_services()
            
        except Exception as e:
            logger.error(f"Manual OAuth flow failed: {e}")
            return False

    def _build_services(self) -> bool:
        """Build YouTube API services."""
        try:
            logger.info("Building YouTube API service")
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            logger.info("YouTube API service built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build services: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return results."""
        results = {
            'authenticated': False,
            'youtube_api': False,
            'channel_access': False,
            'errors': []
        }
        
        if not self.credentials:
            results['errors'].append("No credentials available")
            return results
        
        results['authenticated'] = True
        
        if self.youtube:
            try:
                # Test basic API access
                request = self.youtube.channels().list(part="snippet,statistics", mine=True)
                response = request.execute()
                
                results['youtube_api'] = True
                
                if response.get('items'):
                    results['channel_access'] = True
                    channel = response['items'][0]
                    
                    results['channel_info'] = {
                        'title': channel['snippet']['title'],
                        'id': channel['id'],
                        'description': channel['snippet']['description'][:100] + "..." if len(channel['snippet']['description']) > 100 else channel['snippet']['description'],
                        'subscriber_count': channel['statistics'].get('subscriberCount', 'Hidden'),
                        'video_count': channel['statistics'].get('videoCount', '0'),
                        'view_count': channel['statistics'].get('viewCount', '0')
                    }
                    
                    logger.info(f"Connected to channel: {channel['snippet']['title']}")
                else:
                    results['errors'].append("No channel found for authenticated user")
                    
            except HttpError as e:
                error_msg = f"YouTube API error: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results

    def get_recent_videos(self, max_results: int = 10) -> Optional[Dict[str, Any]]:
        """Get recent videos from the authenticated channel."""
        if not self.youtube:
            logger.error("YouTube API not available")
            return None
        
        try:
            # First get the channel's uploads playlist
            channels_response = self.youtube.channels().list(
                part="contentDetails",
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                logger.error("No channel found")
                return None
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in playlist_response.get('items', []):
                video = {
                    'title': item['snippet']['title'],
                    'video_id': item['snippet']['resourceId']['videoId'],
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'][:100] + "..." if len(item['snippet']['description']) > 100 else item['snippet']['description']
                }
                videos.append(video)
            
            logger.info(f"Retrieved {len(videos)} recent videos")
            return {'videos': videos}
            
        except Exception as e:
            logger.error(f"Failed to get recent videos: {e}")
            return None

    def clear_credentials(self):
        """Clear stored credentials."""
        token_file = self.configs_dir / "token.pickle"
        if token_file.exists():
            token_file.unlink()
            logger.info("Credentials cleared")

def main():
    """Main function for testing."""
    print("YouTube OAuth Simple Client")
    print("=" * 50)
    
    configs_path = Path(__file__).parent.parent / "configs"
    client = YouTubeOAuthSimple(configs_path)
    
    # Test authentication
    if client.authenticate_manual():
        print("✓ Authentication successful!")
        
        # Test connection
        results = client.test_connection()
        
        print("\nConnection Test Results:")
        print("-" * 30)
        
        for key, value in results.items():
            if key == 'errors':
                if value:
                    print("Errors:")
                    for error in value:
                        print(f"  - {error}")
            elif key == 'channel_info':
                if value:
                    print(f"Channel Info:")
                    print(f"  - Title: {value['title']}")
                    print(f"  - ID: {value['id']}")
                    print(f"  - Subscribers: {value['subscriber_count']}")
                    print(f"  - Videos: {value['video_count']}")
                    print(f"  - Total Views: {value['view_count']}")
            else:
                status = "✓" if value else "✗"
                print(f"{status} {key}: {value}")
        
        # Test getting recent videos
        if results['channel_access']:
            print("\nRecent Videos:")
            print("-" * 30)
            videos_data = client.get_recent_videos(5)
            if videos_data:
                for i, video in enumerate(videos_data['videos'], 1):
                    print(f"{i}. {video['title']}")
                    print(f"   Published: {video['published_at']}")
                    print(f"   Video ID: {video['video_id']}")
                    print()
            else:
                print("No videos found or error retrieving videos")
    else:
        print("✗ Authentication failed")

if __name__ == '__main__':
    main()
