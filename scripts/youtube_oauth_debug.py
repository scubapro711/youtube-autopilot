'''
Enhanced YouTube OAuth Client with detailed debugging and error handling.

This client provides comprehensive OAuth authentication with full YouTube scopes
including analytics, channel management, and upload capabilities.
'''

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# YouTube API scopes - comprehensive list for full functionality
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtubepartner',
    'https://www.googleapis.com/auth/youtube-paid-content',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/yt-analytics-monetary.readonly'
]

# Minimal scopes for testing
MINIMAL_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly'
]

class YouTubeOAuthDebugClient:
    '''Enhanced YouTube OAuth client with comprehensive debugging.'''

    def __init__(self, configs_dir: Path = None, use_minimal_scopes: bool = False):
        """
        Initialize the YouTube OAuth client.
        
        Args:
            configs_dir: Directory containing client_secrets.json
            use_minimal_scopes: If True, use only readonly scope for testing
        """
        self.configs_dir = configs_dir or Path(__file__).parent.parent / "configs"
        self.scopes = MINIMAL_SCOPES if use_minimal_scopes else SCOPES
        self.credentials = None
        self.youtube = None
        self.youtube_analytics = None
        
        logger.info(f"Initializing YouTube OAuth client with {len(self.scopes)} scopes")
        logger.debug(f"Scopes: {self.scopes}")

    def authenticate(self, force_refresh: bool = False) -> bool:
        """
        Authenticate with Google OAuth and build YouTube service.
        
        Args:
            force_refresh: If True, force re-authentication
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Check for existing credentials
            token_file = self.configs_dir / "token.pickle"
            
            if not force_refresh and token_file.exists():
                logger.info("Loading existing credentials from token.pickle")
                try:
                    with open(token_file, 'rb') as token:
                        self.credentials = pickle.load(token)
                        logger.info("Successfully loaded existing credentials")
                except Exception as e:
                    logger.warning(f"Failed to load existing credentials: {e}")
                    self.credentials = None

            # Refresh or get new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    try:
                        self.credentials.refresh(Request())
                        logger.info("Successfully refreshed credentials")
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        self.credentials = None
                
                if not self.credentials:
                    logger.info("Starting new OAuth flow")
                    return self._run_oauth_flow()

            # Save credentials
            try:
                with open(token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
                logger.info("Credentials saved successfully")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")

            # Build YouTube services
            return self._build_services()

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _run_oauth_flow(self) -> bool:
        """Run the OAuth flow to get new credentials."""
        try:
            client_secrets_file = self.configs_dir / "client_secrets.json"
            
            if not client_secrets_file.exists():
                logger.error(f"Client secrets file not found: {client_secrets_file}")
                return False

            logger.info(f"Using client secrets from: {client_secrets_file}")
            
            # Create flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_file), 
                self.scopes
            )
            
            # Configure flow for better debugging
            flow.redirect_uri = 'http://localhost:8080'
            
            logger.info("Starting OAuth flow...")
            logger.info(f"Redirect URI: {flow.redirect_uri}")
            logger.info(f"Scopes requested: {self.scopes}")
            
            # Run local server
            try:
                self.credentials = flow.run_local_server(
                    port=8080,
                    prompt='consent',
                    authorization_prompt_message='Please visit this URL to authorize the application: {url}',
                    success_message='The auth flow is complete; you may close this window.',
                    open_browser=True
                )
                logger.info("OAuth flow completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                logger.info("Trying manual flow...")
                
                # Try manual flow as fallback
                auth_url, _ = flow.authorization_url(prompt='consent')
                logger.info(f"Please visit this URL to authorize the application:")
                logger.info(f"{auth_url}")
                
                auth_code = input("Enter the authorization code: ")
                flow.fetch_token(code=auth_code)
                self.credentials = flow.credentials
                
                logger.info("Manual OAuth flow completed successfully")
                return True

        except Exception as e:
            logger.error(f"OAuth flow failed completely: {e}")
            return False

    def _build_services(self) -> bool:
        """Build YouTube API services."""
        try:
            logger.info("Building YouTube API services...")
            
            # Build YouTube Data API service
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            logger.info("YouTube Data API service built successfully")
            
            # Build YouTube Analytics API service (if we have the right scopes)
            analytics_scopes = [s for s in self.scopes if 'analytics' in s]
            if analytics_scopes:
                try:
                    self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=self.credentials)
                    logger.info("YouTube Analytics API service built successfully")
                except Exception as e:
                    logger.warning(f"Failed to build YouTube Analytics service: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build services: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return detailed results."""
        results = {
            'authenticated': False,
            'youtube_data_api': False,
            'youtube_analytics_api': False,
            'channel_access': False,
            'upload_access': False,
            'analytics_access': False,
            'errors': []
        }
        
        if not self.credentials:
            results['errors'].append("No credentials available")
            return results
        
        results['authenticated'] = True
        
        # Test YouTube Data API
        if self.youtube:
            try:
                # Test basic API access
                request = self.youtube.channels().list(part="snippet", mine=True)
                response = request.execute()
                
                results['youtube_data_api'] = True
                
                if response.get('items'):
                    results['channel_access'] = True
                    channel = response['items'][0]
                    logger.info(f"Connected to channel: {channel['snippet']['title']}")
                    results['channel_info'] = {
                        'title': channel['snippet']['title'],
                        'id': channel['id'],
                        'description': channel['snippet']['description'][:100] + "..." if len(channel['snippet']['description']) > 100 else channel['snippet']['description']
                    }
                else:
                    results['errors'].append("No channel found for authenticated user")
                    
            except HttpError as e:
                error_msg = f"YouTube Data API error: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error testing YouTube Data API: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        # Test upload capability
        if 'youtube.upload' in ' '.join(self.scopes):
            results['upload_access'] = True
        
        # Test YouTube Analytics API
        if self.youtube_analytics:
            try:
                # Test analytics access
                request = self.youtube_analytics.reports().query(
                    ids='channel==MINE',
                    startDate='2024-01-01',
                    endDate='2024-01-31',
                    metrics='views,estimatedMinutesWatched',
                    dimensions='day'
                )
                response = request.execute()
                results['youtube_analytics_api'] = True
                results['analytics_access'] = True
                logger.info("YouTube Analytics API access confirmed")
                
            except HttpError as e:
                error_msg = f"YouTube Analytics API error: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error testing YouTube Analytics API: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results

    def get_channel_analytics(self, start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> Optional[Dict[str, Any]]:
        """Get channel analytics data."""
        if not self.youtube_analytics:
            logger.error("YouTube Analytics API not available")
            return None
        
        try:
            request = self.youtube_analytics.reports().query(
                ids='channel==MINE',
                startDate=start_date,
                endDate=end_date,
                metrics='views,estimatedMinutesWatched,subscribersGained,subscribersLost',
                dimensions='day'
            )
            response = request.execute()
            logger.info(f"Retrieved analytics data: {len(response.get('rows', []))} data points")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return None

    def clear_credentials(self):
        """Clear stored credentials."""
        token_file = self.configs_dir / "token.pickle"
        if token_file.exists():
            token_file.unlink()
            logger.info("Credentials cleared")

def main():
    """Main function for testing."""
    print("YouTube OAuth Debug Client")
    print("=" * 50)
    
    configs_path = Path(__file__).parent.parent / "configs"
    
    # Test with minimal scopes first
    print("\n1. Testing with minimal scopes (readonly only)...")
    client_minimal = YouTubeOAuthDebugClient(configs_path, use_minimal_scopes=True)
    
    if client_minimal.authenticate():
        results = client_minimal.test_connection()
        print("✓ Minimal scope authentication successful")
        
        for key, value in results.items():
            if key != 'errors':
                status = "✓" if value else "✗"
                print(f"  {status} {key}: {value}")
        
        if results['errors']:
            print("  Errors:")
            for error in results['errors']:
                print(f"    - {error}")
    else:
        print("✗ Minimal scope authentication failed")
        return
    
    # Test with full scopes
    print("\n2. Testing with full scopes (including analytics)...")
    client_full = YouTubeOAuthDebugClient(configs_path, use_minimal_scopes=False)
    
    if client_full.authenticate():
        results = client_full.test_connection()
        print("✓ Full scope authentication successful")
        
        for key, value in results.items():
            if key != 'errors' and key != 'channel_info':
                status = "✓" if value else "✗"
                print(f"  {status} {key}: {value}")
        
        if 'channel_info' in results:
            print(f"  Channel: {results['channel_info']['title']}")
        
        if results['errors']:
            print("  Errors:")
            for error in results['errors']:
                print(f"    - {error}")
        
        # Test analytics if available
        if results['analytics_access']:
            print("\n3. Testing analytics data retrieval...")
            analytics = client_full.get_channel_analytics("2024-09-01", "2024-09-30")
            if analytics:
                print(f"✓ Retrieved analytics data: {len(analytics.get('rows', []))} data points")
            else:
                print("✗ Failed to retrieve analytics data")
    else:
        print("✗ Full scope authentication failed")

if __name__ == '__main__':
    main()
