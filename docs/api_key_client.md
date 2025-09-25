# YouTube API Key Client

This document provides an overview of the `youtube_client_apikey.py` script, which offers a simplified way to interact with the YouTube Data API using an API key.

## Overview

The API key client is designed for read-only operations that do not require user authentication (OAuth2). It is suitable for tasks such as:

- Searching for videos
- Retrieving video details (statistics, content details)
- Getting channel information
- Fetching popular videos

## Authentication

This client uses a simple API key for authentication. The key is loaded from the `configs/api_key.txt` file. 

**Important:** The API key should be kept confidential and should not be hard-coded into the script. It is recommended to restrict the API key to the YouTube Data API v3 to prevent unauthorized use.

## Usage

To use the client, you first need to create an instance of the `YouTubeClientAPIKey` class:

```python
from pathlib import Path
from scripts.youtube_client_apikey import YouTubeClientAPIKey

configs_path = Path(__file__).parent.parent / "configs"
client = YouTubeClientAPIKey(configs_dir=configs_path)
```

Once the client is initialized, you can use its methods to interact with the YouTube API:

```python
# Search for videos
videos = client.search_videos("Python programming", max_results=5)

# Get video details
details = client.get_video_details("VIDEO_ID")

# Get channel information
channel_info = client.get_channel_info_by_id("CHANNEL_ID")
```

## Configuration

The API key is configured in the `configs/config.yaml` file under the `api_key` field. The `youtube_client_apikey.py` script will automatically load the key from this file.

```yaml
# API Key for YouTube Data API
api_key: "YOUR_API_KEY"
```

## Limitations

Since this client uses an API key, it is limited to read-only operations. It cannot be used for actions that require user authorization, such as:

- Uploading videos
- Managing playlists
- Commenting on videos
- Liking or disliking videos

For these operations, the OAuth2-based client (`youtube_client.py`) should be used.

