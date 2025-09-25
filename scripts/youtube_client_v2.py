'''
Enhanced YouTube API Client for the YouTube Autopilot project.

Supports both OAuth 2.0 and Service Account authentication methods.
Handles authentication issues gracefully with fallback mechanisms.
'''

import os
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube"
]
CLIENT_SECRETS_FILE = "client_secrets.json"
SERVICE_ACCOUNT_FILE = "service_account.json"
TOKEN_PICKLE_FILE = "token.pickle"

class YouTubeClientV2:
    '''Enhanced YouTube API client with multiple authentication methods.'''

    def __init__(self, configs_dir: Path, auth_method: str = "auto"):
        """
        Initialize the YouTube client.
        
        Args:
            configs_dir: Directory containing configuration files
            auth_method: Authentication method ("oauth", "service_account", or "auto")
        """
        self.configs_dir = configs_dir
        self.auth_method = auth_method
        self.credentials = None
        self.youtube = None
        
        # Initialize authentication
        self._authenticate()
        
        if self.credentials:
            self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=self.credentials)
            logger.info("YouTube client initialized successfully")
        else:
            logger.error("Failed to initialize YouTube client - no valid credentials")

    def _authenticate(self):
        """Authenticate using the specified or best available method."""
        if self.auth_method == "auto":
            # Try service account first, then OAuth
            self.credentials = self._try_service_account_auth()
            if not self.credentials:
                self.credentials = self._try_oauth_auth()
        elif self.auth_method == "service_account":
            self.credentials = self._try_service_account_auth()
        elif self.auth_method == "oauth":
            self.credentials = self._try_oauth_auth()
        else:
            raise ValueError(f"Invalid auth_method: {self.auth_method}")

    def _try_service_account_auth(self) -> Optional[service_account.Credentials]:
        """Try to authenticate using service account credentials."""
        service_account_path = self.configs_dir / SERVICE_ACCOUNT_FILE
        
        if not service_account_path.exists():
            logger.info(f"Service account file not found at {service_account_path}")
            return None
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(service_account_path),
                scopes=SCOPES
            )
            logger.info("Successfully authenticated using service account")
            return credentials
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            return None

    def _try_oauth_auth(self) -> Optional[Credentials]:
        """Try to authenticate using OAuth 2.0 flow."""
        creds = None
        token_path = self.configs_dir / TOKEN_PICKLE_FILE
        client_secrets_path = self.configs_dir / CLIENT_SECRETS_FILE

        # Load existing token if available
        if token_path.exists():
            try:
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing OAuth credentials")
            except Exception as e:
                logger.error(f"Failed to load existing token: {e}")

        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Successfully refreshed OAuth credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            # If still no valid credentials, try OAuth flow
            if not creds:
                if not client_secrets_path.exists():
                    logger.error(f"Client secrets file not found at {client_secrets_path}")
                    return None
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secrets_path), SCOPES
                    )
                    # Use a different port to avoid conflicts
                    creds = flow.run_local_server(port=8080, open_browser=False)
                    logger.info("Successfully completed OAuth flow")
                    
                    # Save the credentials for future use
                    with open(token_path, "wb") as token:
                        pickle.dump(creds, token)
                    logger.info("Saved OAuth credentials for future use")
                    
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return None

        return creds

    def upload_video(self, file_path: str, title: str, description: str, 
                    tags: List[str], category_id: str = "22", 
                    privacy_status: str = "private") -> Optional[Dict[str, Any]]:
        """Upload a video to YouTube."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        if not os.path.exists(file_path):
            logger.error(f"Video file not found: {file_path}")
            return None
        
        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }

            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")

            logger.info(f"Video uploaded successfully! Video ID: {response['id']}")
            return response
            
        except HttpError as e:
            logger.error(f"HTTP error during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated channel."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]
            else:
                logger.warning("No channel found for authenticated user")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error getting channel info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting channel info: {e}")
            return None

    def get_channel_videos(self, max_results: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get a list of videos from the authenticated channel."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            # First get the channel's upload playlist ID
            channel_info = self.get_channel_info()
            if not channel_info:
                return None
            
            uploads_playlist_id = channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get videos from the uploads playlist
            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            )
            response = request.execute()
            
            return response.get("items", [])
            
        except HttpError as e:
            logger.error(f"HTTP error getting channel videos: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting channel videos: {e}")
            return None

    def get_video_analytics(self, video_id: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Get analytics data for a specific video."""
        if not self.youtube:
            logger.error("YouTube client not initialized")
            return None
        
        try:
            # Note: This requires YouTube Analytics API to be enabled
            # For now, we'll get basic video statistics
            request = self.youtube.videos().list(
                part="statistics",
                id=video_id
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]["statistics"]
            else:
                logger.warning(f"No statistics found for video ID: {video_id}")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error getting video analytics: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting video analytics: {e}")
            return None

    def test_connection(self) -> bool:
        """Test the YouTube API connection."""
        try:
            channel_info = self.get_channel_info()
            if channel_info:
                logger.info(f"Connection test successful. Channel: {channel_info['snippet']['title']}")
                return True
            else:
                logger.error("Connection test failed - no channel info retrieved")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

def create_service_account_file(configs_dir: Path, project_id: str, 
                               service_account_email: str, private_key: str) -> bool:
    """Create a service account JSON file from provided credentials."""
    service_account_path = configs_dir / SERVICE_ACCOUNT_FILE
    
    service_account_data = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "generated",
        "private_key": private_key,
        "client_email": service_account_email,
        "client_id": "generated",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
    
    try:
        with open(service_account_path, 'w') as f:
            json.dump(service_account_data, f, indent=2)
        logger.info(f"Service account file created at {service_account_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create service account file: {e}")
        return False

if __name__ == '__main__':
    # Example usage
    configs_path = Path(__file__).parent.parent / "configs"
    
    print("Testing YouTube API Client V2...")
    print("=" * 50)
    
    # Try different authentication methods
    for auth_method in ["auto", "service_account", "oauth"]:
        print(f"\nTesting with auth_method: {auth_method}")
        try:
            client = YouTubeClientV2(configs_dir=configs_path, auth_method=auth_method)
            if client.credentials:
                print(f"✓ Authentication successful with {auth_method}")
                
                # Test connection
                if client.test_connection():
                    print("✓ Connection test passed")
                    break
                else:
                    print("✗ Connection test failed")
            else:
                print(f"✗ Authentication failed with {auth_method}")
        except Exception as e:
            print(f"✗ Error with {auth_method}: {e}")
    
    print("\nTest completed.")
