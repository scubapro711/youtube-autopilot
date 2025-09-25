'''
YouTube API Client for the YouTube Autopilot project.

Handles authentication, video uploads, and analytics data retrieval.
'''

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Constants
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS_FILE = "client_secrets.json" # This file should be in the configs directory
TOKEN_PICKLE_FILE = "token.pickle"

class YouTubeClient:
    '''A client for interacting with the YouTube Data API v3.'''

    def __init__(self, configs_dir: Path):
        self.configs_dir = configs_dir
        self.credentials = self._get_credentials()
        self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=self.credentials)

    def _get_credentials(self) -> Optional[Credentials]:
        '''Gets valid user credentials from storage or runs the OAuth2 flow.'''
        creds = None
        token_path = self.configs_dir / TOKEN_PICKLE_FILE
        client_secrets_path = self.configs_dir / CLIENT_SECRETS_FILE

        if token_path.exists():
            with open(token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not client_secrets_path.exists():
                    print(f"ERROR: Client secrets file not found at {client_secrets_path}")
                    print("Please download your client_secrets.json from the Google Cloud Console and place it in the configs directory.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def upload_video(self, file_path: str, title: str, description: str, tags: List[str], category_id: str, privacy_status: str) -> Optional[Dict[str, Any]]:
        '''Uploads a video to YouTube.'''
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
                    print(f"Uploaded {int(status.progress() * 100)}%")

            print(f"Video uploaded successfully! Video ID: {response['id']}")
            return response
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None

    def get_channel_analytics(self, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        '''Retrieves channel analytics data.'''
        try:
            request = self.youtube.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,comments,likes,dislikes,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
                dimensions="day"
            )
            response = request.execute()
            return response
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return None

if __name__ == '__main__':
    # This is an example of how to use the client
    # You would need to have your client_secrets.json file in the configs directory
    configs_path = Path(__file__).parent.parent / "configs"
    if not (configs_path / CLIENT_SECRETS_FILE).exists():
        print(f"Please place your '{CLIENT_SECRETS_FILE}' in the '{configs_path}' directory to run this example.")
    else:
        client = YouTubeClient(configs_dir=configs_path)
        if client.credentials:
            print("YouTube client initialized successfully.")
            # Example usage:
            # analytics = client.get_channel_analytics(start_date="2025-09-01", end_date="2025-09-25")
            # if analytics:
            #     print(analytics)

