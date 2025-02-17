import json
from datetime import datetime
import os
from pathlib import Path
# emulates the following curl requests:
#curl -X POST "https://accounts.spotify.com/api/token" \
#     -H "Content-Type: application/x-www-form-urlencoded" \
#     -d "grant_type=client_credentials&client_id=your-client-id&client_secret=your-client-secret"
# and with bearer token:
#curl -X GET "https://api.spotify.com/v1/artists/16SiO2DZeffJZAKlppdOAw" \
#     -H "Authorization: Bearer {your_access_token}"

import requests
import sys

# Token management
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
bearer_token = None
bearer_token_expires = None

def get_data_directory():
    """Get the data directory path (for token storage only)"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def get_current_date_string():
    return datetime.now().strftime("%Y-%m-%d")

def load_cached_token():
    data_dir = get_data_directory()
    token_file = data_dir / "bearer_token.json"
    
    if not token_file.exists():
        return None, None
        
    try:
        with open(token_file) as f:
            token_data = json.load(f)
            
        token_time = datetime.fromisoformat(token_data['timestamp'])
        if (datetime.now() - token_time).total_seconds() < 3600:
            return token_data['token'], token_data['expires']
            
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error reading cached token: {e}")
    
    return None, None

def save_token(token, expires):
    data_dir = get_data_directory()
    token_file = data_dir / "bearer_token.json"
    
    token_data = {
        'token': token,
        'expires': expires,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=4)

def ensure_valid_token():
    global bearer_token, bearer_token_expires
    
    if bearer_token is None:
        bearer_token, bearer_token_expires = load_cached_token()
    
    if bearer_token is None:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        token_data = response.json()
        
        bearer_token = token_data["access_token"]
        bearer_token_expires = token_data.get("expires_in", 3600)
        
        save_token(bearer_token, bearer_token_expires)
    
    return bearer_token

def get_artist_data(artist_id='16SiO2DZeffJZAKlppdOAw'):
    token = ensure_valid_token()
    data_dir = get_data_directory()
    current_date = get_current_date_string()
    filename = f"{current_date}__artist_data.json"
    filepath = data_dir / filename
    
    if filepath.exists():
        print(f"Found existing artist data for today in {filename}")
        with open(filepath) as f:
            return json.load(f)
    
    try:
        response = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        data = response.json()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        sys.exit(1)

def get_all_artist_albums(artist_id='16SiO2DZeffJZAKlppdOAw'):
    """Get all albums (both full albums and singles) for an artist"""
    token = ensure_valid_token()
    
    try:
        all_items = []
        offset = 0
        limit = 50
        
        while True:
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
            
            if data['next'] is None:
                break
                
            offset += limit
        
        return all_items
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting albums: {e}")
        sys.exit(1)

def get_album_tracks(album_id):
    """Get all tracks for a specific album"""
    token = ensure_valid_token()
    
    try:
        all_items = []
        offset = 0
        limit = 50
        
        while True:
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
            
            if data['next'] is None:
                break
                
            offset += limit
        
        return all_items
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting album tracks: {e}")
        sys.exit(1)

def get_album_id_from_artist_albums(artist_albums):
    album_ids = [album['id'] for album in artist_albums]
    return album_ids

def cleanup_old_files():
    data_dir = get_data_directory()
    current_date = get_current_date_string()
    
    # Get all json files in the data directory
    for file in data_dir.glob("*.json"):
        # If the file doesn't start with today's date, delete it
        if not file.name.startswith(current_date):
            print(f"Removing old file: {file.name}")
            file.unlink()

def populate_artist_data():
    cleanup_old_files()
    
    # Get initial token
    token = ensure_valid_token()
    
    artist_data = get_artist_data()
    print(json.dumps(artist_data, indent=4))
    artist_albums = get_all_artist_albums()

    print(json.dumps(artist_albums, indent=4))
    album_ids = get_album_id_from_artist_albums(artist_albums)
    print(album_ids)
    for album_id in album_ids:
        album_tracks = get_album_tracks(album_id)
        print(json.dumps(album_tracks, indent=4))

def get_artist_tracks(artist_id='16SiO2DZeffJZAKlppdOAw'):
    token = ensure_valid_token()
    data_dir = get_data_directory()
    current_date = get_current_date_string()
    albums_filename = f"{current_date}__artist_albums.json"
    albums_filepath = data_dir / albums_filename
    
    try:
        all_albums = []
        all_tracks = []
        albums_offset = 0
        
        # Get all albums and singles with pagination
        while True:
            albums_response = requests.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/albums",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "include_groups": "album,single",
                    "limit": 50,
                    "offset": albums_offset,
                    "market": "US"
                }
            )
            albums_response.raise_for_status()
            albums_data = albums_response.json()
            
            # Extend all_albums list
            all_albums.extend(albums_data['items'])
            
            # For each album/single in this page, get all tracks
            for album in albums_data['items']:
                tracks_offset = 0
                while True:
                    tracks_response = requests.get(
                        f"https://api.spotify.com/v1/albums/{album['id']}/tracks",
                        headers={"Authorization": f"Bearer {token}"},
                        params={
                            "limit": 50,
                            "offset": tracks_offset,
                            "market": "US"
                        }
                    )
                    tracks_response.raise_for_status()
                    tracks_data = tracks_response.json()
                    
                    # Add album details to each track and save individual files
                    for track in tracks_data['items']:
                        track['album_name'] = album['name']
                        track['album_type'] = album['album_type']
                        track['release_date'] = album['release_date']
                        
                        # Create individual track file
                        track_name = track['name']
                        safe_track_name = "".join(c for c in track_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        safe_track_name = safe_track_name.replace(' ', '-')
                        track_filename = f"{current_date}__track__{safe_track_name}_{track['id']}.json"
                        track_filepath = data_dir / track_filename
                        
                        if not track_filepath.exists():
                            track_data = {
                                'items': [track],
                                'total': 1,
                                'limit': 1,
                                'offset': 0
                            }
                            with open(track_filepath, 'w') as f:
                                json.dump(track_data, f, indent=4)
                        
                        all_tracks.append(track)
                    
                    if not tracks_data['next']:
                        break
                        
                    tracks_offset += 50
            
            if not albums_data['next']:
                break
                
            albums_offset += 50
        
        # Save albums data
        albums_complete_data = {
            'items': all_albums,
            'total': len(all_albums),
            'limit': 50,
            'offset': 0
        }
        
        if not albums_filepath.exists():
            with open(albums_filepath, 'w') as f:
                json.dump(albums_complete_data, f, indent=4)
        
        return {'items': all_tracks, 'total': len(all_tracks), 'artist_id': artist_id}
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cleanup_old_files()
    
    # Get initial token
    print("Getting initial token")
    token = ensure_valid_token()
    print("Token obtained")

    print("Getting artist data")
    artist_data = get_artist_data()
    print("Artist data obtained")
    #print(json.dumps(artist_data, indent=4))
    
    # Get artist tracks
    print("Getting artist tracks")
    artist_tracks = get_artist_tracks()
    print(f"Total tracks found: {len(artist_tracks['items'])}")
    #rint(json.dumps(artist_tracks, indent=4))
    
