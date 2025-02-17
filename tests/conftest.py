import pytest
from pathlib import Path
import sqlite3
import json
from unittest.mock import Mock

@pytest.fixture
def monkeypatch(request):
    """Fixture to provide monkeypatch"""
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    request.addfinalizer(mpatch.undo)
    return mpatch

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path"""
    return tmp_path / "test.db"

@pytest.fixture
def mock_spotify_response():
    """Mock Spotify API response data"""
    return {
        "id": "test_id",
        "name": "Test Album",
        "release_date": "2025-01-01",
        "total_tracks": 10,
        "external_urls": {"spotify": "https://open.spotify.com/album/test"},
        "uri": "spotify:album:test",
        "album_type": "album",
        "images": [
            {"url": "https://example.com/large.jpg"},
            {"url": "https://example.com/medium.jpg"},
            {"url": "https://example.com/small.jpg"}
        ]
    }

@pytest.fixture
def mock_track_response():
    """Mock Spotify track response data"""
    return {
        "id": "track_id",
        "name": "Test Track",
        "duration_ms": 180000,
        "track_number": 1,
        "external_urls": {"spotify": "https://open.spotify.com/track/test"},
        "uri": "spotify:track:test",
        "images": [
            {"url": "https://example.com/large.jpg"},
            {"url": "https://example.com/medium.jpg"},
            {"url": "https://example.com/small.jpg"}
        ]
    }

@pytest.fixture
def mock_spotify_client(mocker, mock_spotify_response, mock_track_response):
    """Create a mock SpotifyClient"""
    mock_client = Mock()
    mock_client.get_artist_data.return_value = {"name": "Test Artist"}
    mock_client.get_all_artist_albums.return_value = [mock_spotify_response]
    mock_client.get_album_tracks.return_value = [mock_track_response]
    return mock_client
