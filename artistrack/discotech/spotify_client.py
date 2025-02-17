import json
from datetime import datetime
import os
from pathlib import Path
import requests
import sys
from typing import Dict, List, Any

class SpotifyApiError(Exception):
    """Custom exception for Spotify API errors"""
    pass

class SpotifyClient:
    def __init__(self, verbose: bool = False):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.verbose = verbose
        
        if not self.client_id or not self.client_secret:
            print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables must be set")
            sys.exit(1)
            
        self.bearer_token = None
        self.bearer_token_expires = None
        
    def get_data_directory(self) -> Path:
        """Get the data directory path"""
        # Get the path to the artistrack/data directory
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def load_cached_token(self):
        data_dir = self.get_data_directory()
        token_file = data_dir / "bearer_token.json"
        
        if not token_file.exists():
            if self.verbose:
                print("No cached token found")
            return None, None
            
        try:
            with open(token_file) as f:
                token_data = json.load(f)
                
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if (datetime.now() - token_time).total_seconds() < 3600:
                if self.verbose:
                    print("Using cached token:", json.dumps(token_data, indent=2))
                return token_data['token'], token_data['expires']
            elif self.verbose:
                print("Cached token expired")
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error reading cached token: {e}")
        
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

    def get_artist_data(self, artist_id='16SiO2DZeffJZAKlppdOAw') -> Dict[str, Any]:
        """Get artist data from Spotify API"""
        token = self.ensure_valid_token()
        data_dir = self.get_data_directory()
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"{current_date}__artist_data.json"
        filepath = data_dir / filename
        
        if filepath.exists():
            print(f"Found existing artist data for today in {filename}")
            with open(filepath) as f:
                data = json.load(f)
                if self.verbose:
                    print("Artist data:", json.dumps(data, indent=2))
                return data
        
        try:
            if self.verbose:
                print(f"Fetching artist data for {artist_id}...")
                
            response = requests.get(
                f"https://api.spotify.com/v1/artists/{artist_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
                
            if self.verbose:
                print("Received artist data:", json.dumps(data, indent=2))
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching artist data: {e}")
            sys.exit(1)

    def get_all_artist_albums(self, artist_id='16SiO2DZeffJZAKlppdOAw') -> List[Dict[str, Any]]:
        """Get all albums (both full albums and singles) for an artist"""
        token = self.ensure_valid_token()
        
        try:
            all_items = []
            offset = 0
            limit = 50
            
            while True:
                if self.verbose:
                    print(f"Fetching albums (offset={offset}, limit={limit})...")
                    
                response = requests.get(
                    f"https://api.spotify.com/v1/artists/{artist_id}/albums",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "include_groups": "album,single",
                        "limit": limit,
                        "offset": offset,
                        "market": "US"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                all_items.extend(data['items'])
                
                if self.verbose:
                    print(f"Received {len(data['items'])} albums")
                    print("Album data:", json.dumps(data, indent=2))
                
                if data['next'] is None:
                    break
                    
                offset += limit
            
            return all_items
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching artist albums: {e}")
            sys.exit(1)

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
