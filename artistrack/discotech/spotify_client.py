import json
from datetime import datetime
import os
from pathlib import Path
import requests
import sys
from typing import Dict, List, Any, Tuple, Optional

class SpotifyApiError(Exception):
    """Custom exception for Spotify API errors"""
    pass

class SpotifyClient:
    """Client for interacting with Spotify API"""
    
    def __init__(self, artist_id='16SiO2DZeffJZAKlppdOAw', verbose=False):
        """Initialize the client"""
        self.artist_id = artist_id
        self.verbose = verbose
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables must be set")
        
        self.bearer_token = None
        self.bearer_token_expires = None
        
    def get_data_directory(self) -> Path:
        """Get the data directory path"""
        # Get the path to the artistrack/data directory
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def load_cached_token(self) -> Tuple[Optional[str], Optional[datetime]]:
        """Load cached bearer token from file"""
        token_path = self.get_data_directory() / 'bearer_token.json'
        
        if not token_path.exists():
            return None, None
        
        try:
            with open(token_path, 'r') as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data['timestamp'])
                if timestamp > datetime.now():
                    return data['token'], timestamp
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Error reading cached token: {e}")
            return None, None
        except Exception as e:
            if self.verbose:
                print(f"Unexpected error reading token: {e}")
            return None, None
        
        return None, None

    def save_token(self, token, expires):
        data_dir = self.get_data_directory()
        token_file = data_dir / "bearer_token.json"
        
        token_data = {
            'token': token,
            'expires': expires,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=4)

    def ensure_valid_token(self) -> str:
        if self.bearer_token is None:
            self.bearer_token, self.bearer_token_expires = self.load_cached_token()
        
        if self.bearer_token is None:
            try:
                if self.verbose:
                    print("Requesting new token from Spotify API...")
                    
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = requests.post(
                    "https://accounts.spotify.com/api/token",
                    headers=headers,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                response.raise_for_status()
                token_data = response.json()
                
                self.bearer_token = token_data["access_token"]
                self.bearer_token_expires = token_data.get("expires_in", 3600)
                
                if self.verbose:
                    print("Received new token:", json.dumps(token_data, indent=2))
                
                self.save_token(self.bearer_token, self.bearer_token_expires)
            except requests.exceptions.RequestException as e:
                print(f"Error obtaining Spotify token: {e}")
                sys.exit(1)
        
        return self.bearer_token

    def get_artist_data(self) -> Dict[str, Any]:
        """Get artist data from Spotify API or cache"""
        token = self.ensure_valid_token()
        
        # Check for cached data
        data_file = self.get_data_directory() / f"{datetime.now().strftime('%Y-%m-%d')}__artist_data.json"
        
        try:
            if data_file.exists():
                if self.verbose:
                    print(f"Found existing artist data for today in {data_file.name}")
                with open(data_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            if self.verbose:
                print(f"Error reading cached artist data: {e}")
        
        # Fetch from API
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"https://api.spotify.com/v1/artists/{self.artist_id}",
            headers=headers
        )
        response.raise_for_status()
        
        # Cache the response
        artist_data = response.json()
        try:
            with open(data_file, 'w') as f:
                json.dump(artist_data, f, indent=2)
        except OSError as e:
            if self.verbose:
                print(f"Error caching artist data: {e}")
        
        return artist_data

    def get_all_artist_albums(self) -> List[Dict[str, Any]]:
        """Get all albums (both full albums and singles) for an artist"""
        token = self.ensure_valid_token()
        
        all_albums = []
        next_url = f"https://api.spotify.com/v1/artists/{self.artist_id}/albums?limit=50"
        
        while next_url:
            response = requests.get(
                next_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            all_albums.extend(data['items'])
            next_url = data.get('next')
        
        return all_albums

    def get_album_tracks(self, album_id: str) -> List[Dict[str, Any]]:
        """Get all tracks for a specific album"""
        token = self.ensure_valid_token()
        
        try:
            all_items = []
            offset = 0
            limit = 50
            
            while True:
                if self.verbose:
                    print(f"Fetching tracks for album {album_id} (offset={offset}, limit={limit})...")
                    
                response = requests.get(
                    f"https://api.spotify.com/v1/albums/{album_id}/tracks",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "limit": limit,
                        "offset": offset,
                        "market": "US"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                all_items.extend(data['items'])
                
                if self.verbose:
                    print(f"Received {len(data['items'])} tracks")
                    print("Track data:", json.dumps(data, indent=2))
                
                if data['next'] is None:
                    break
                    
                offset += limit
            
            return all_items
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching album tracks: {e}")
            sys.exit(1)
