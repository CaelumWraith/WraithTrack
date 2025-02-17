import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
from artistrack.discotech.spotify_client import SpotifyClient

@pytest.fixture
def mock_spotify_env(monkeypatch):
    """Mock Spotify environment variables"""
    monkeypatch.setenv('SPOTIFY_CLIENT_ID', 'test_id')
    monkeypatch.setenv('SPOTIFY_CLIENT_SECRET', 'test_secret')

@pytest.fixture
def mock_token_response():
    """Mock Spotify token response"""
    return {
        "access_token": "test_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }

@pytest.fixture
def mock_path():
    """Create a mock Path that supports division operator"""
    class MockPath:
        def __init__(self, path):
            self.path = path
        
        def __truediv__(self, other):
            return MockPath(f"{self.path}/{other}")
        
        def exists(self):
            return False
        
        @property
        def parent(self):
            return MockPath("/parent")
        
        def mkdir(self, *args, **kwargs):
            pass
    
    return MockPath("/test")

def test_get_artist_data(mocker, mock_spotify_env, mock_token_response, mock_path):
    """Test getting artist data from Spotify"""
    # Mock token response
    mock_token = Mock()
    mock_token.json.return_value = mock_token_response
    mock_token.status_code = 200
    
    # Mock artist response
    mock_artist = Mock()
    mock_artist.json.return_value = {"name": "Test Artist"}
    mock_artist.status_code = 200
    
    # Mock requests to return different responses for token and artist
    def mock_get(*args, **kwargs):
        if 'accounts.spotify.com' in args[0]:
            return mock_token
        return mock_artist
    
    def mock_post(*args, **kwargs):
        return mock_token
    
    mocker.patch('requests.get', side_effect=mock_get)
    mocker.patch('requests.post', side_effect=mock_post)
    
    # Mock file operations
    mocker.patch('pathlib.Path', return_value=mock_path)
    
    client = SpotifyClient()
    
    with patch('builtins.open', mock_open()):
        result = client.get_artist_data()
    
    assert result == {"name": "Test Artist"}

def test_get_all_artist_albums(mocker, mock_spotify_env, mock_token_response, mock_spotify_response, mock_path):
    """Test getting all albums for an artist"""
    # Mock token response
    mock_token = Mock()
    mock_token.json.return_value = mock_token_response
    mock_token.status_code = 200
    
    # Mock albums response
    mock_albums = Mock()
    mock_albums.json.return_value = {
        "items": [mock_spotify_response],
        "total": 1,
        "next": None
    }
    mock_albums.status_code = 200
    
    # Mock requests
    def mock_get(*args, **kwargs):
        if 'accounts.spotify.com' in args[0]:
            return mock_token
        return mock_albums
    
    def mock_post(*args, **kwargs):
        return mock_token
    
    mocker.patch('requests.get', side_effect=mock_get)
    mocker.patch('requests.post', side_effect=mock_post)
    mocker.patch('pathlib.Path', return_value=mock_path)
    
    client = SpotifyClient()
    
    with patch('builtins.open', mock_open()):
        albums = client.get_all_artist_albums()
    
    assert len(albums) == 1
    assert albums[0]["name"] == mock_spotify_response["name"]

def test_get_album_tracks(mocker, mock_spotify_env, mock_token_response, mock_track_response, mock_path):
    """Test getting tracks for an album"""
    # Mock token response
    mock_token = Mock()
    mock_token.json.return_value = mock_token_response
    mock_token.status_code = 200
    
    # Mock tracks response
    mock_tracks = Mock()
    mock_tracks.json.return_value = {
        "items": [mock_track_response],
        "total": 1,
        "next": None,  # Add the next field
        "offset": 0,
        "limit": 50
    }
    mock_tracks.status_code = 200
    
    # Mock requests
    def mock_get(*args, **kwargs):
        if 'accounts.spotify.com' in args[0]:
            return mock_token
        return mock_tracks
    
    def mock_post(*args, **kwargs):
        return mock_token
    
    mocker.patch('requests.get', side_effect=mock_get)
    mocker.patch('requests.post', side_effect=mock_post)
    mocker.patch('pathlib.Path', return_value=mock_path)
    
    client = SpotifyClient()
    
    with patch('builtins.open', mock_open()):
        tracks = client.get_album_tracks("test_album_id")
    
    assert len(tracks) == 1
    assert tracks[0]["name"] == mock_track_response["name"]
