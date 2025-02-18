import pytest
import sqlite3
from pathlib import Path
from artistrack.data.listdb import list_db_contents
from artistrack.data.model import init_db

@pytest.fixture
def test_db_path(tmp_path):
    """Create a test database path"""
    return tmp_path / "test.db"

def test_list_db_contents(test_db_path, capsys, monkeypatch):
    """Test listing database contents"""
    # Initialize test database
    init_db(test_db_path)
    
    # Connect to database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Add test data
    cursor.execute("""
        INSERT INTO albums (
            album_id, name, release_date, spotify_url, spotify_uri, qr_code_url,
            track_count, album_type, image_large_uri, image_medium_uri, image_thumb_uri
        ) VALUES (
            'album1', 'Test Album', '2024-01-01', 'http://spotify/album1', 
            'spotify:album:1', 'http://qr/album1', 10, 'album',
            'http://img/large1', 'http://img/medium1', 'http://img/thumb1'
        )
    """)
    
    cursor.execute("""
        INSERT INTO songs (
            song_id, album_id, name, release_date, track_number, duration_ms,
            duration, spotify_url, spotify_uri, qr_code_url, is_single,
            image_large_uri, image_medium_uri, image_thumb_uri
        ) VALUES (
            'song1', 'album1', 'Test Song', '2024-01-01', 1, 180000,
            '3:00', 'http://spotify/song1', 'spotify:track:1', 'http://qr/song1',
            0, 'http://img/large1', 'http://img/medium1', 'http://img/thumb1'
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Mock get_db_path to return test path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.data.listdb.get_db_path', mock_db_path)
    
    # Call function
    list_db_contents()
    
    # Check output
    captured = capsys.readouterr()
    assert "Test Album" in captured.out
    assert "Test Song" in captured.out

def test_list_empty_db(test_db_path, capsys, monkeypatch):
    """Test listing empty database"""
    # Initialize empty test database
    init_db(test_db_path)
    
    # Mock get_db_path to return test path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.data.listdb.get_db_path', mock_db_path)
    
    # Call function
    list_db_contents()
    
    # Check output
    captured = capsys.readouterr()
    assert "No albums found" in captured.out
