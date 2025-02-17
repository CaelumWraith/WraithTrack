import pytest
import sqlite3
from pathlib import Path
from artistrack.data.listdb import list_db_contents
from artistrack.data.model import init_db

def test_list_db_contents(test_db_path, capsys, monkeypatch):
    """Test listing database contents"""
    # Create test database with sample data
    init_db(test_db_path)
    
    # Insert test data
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO albums (
            album_id, name, release_date, spotify_url, spotify_uri,
            qr_code_url, track_count, album_type, image_large_uri,
            image_medium_uri, image_thumb_uri
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'album1', 'Test Album', '2025-01-01',
        'https://spotify/album1', 'spotify:album:1',
        'https://qr/album1', 2, 'album',
        'https://img/large1', 'https://img/medium1', 'https://img/thumb1'
    ))
    
    cursor.execute('''
        INSERT INTO songs (
            song_id, album_id, name, release_date, track_number,
            duration_ms, duration, spotify_url, spotify_uri, qr_code_url,
            is_single, image_large_uri, image_medium_uri, image_thumb_uri
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'song1', 'album1', 'Test Song 1', '2025-01-01', 1,
        180000, '3:00', 'https://spotify/song1', 'spotify:track:1',
        'https://qr/song1', False, 'https://img/large1', 'https://img/medium1',
        'https://img/thumb1'
    ))
    
    conn.commit()
    conn.close()
    
    # Mock get_db_path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.data.listdb.get_db_path', mock_db_path)
    
    # Call the function
    list_db_contents()
    
    # Check output
    captured = capsys.readouterr()
    output = captured.out.lower()
    assert "test album" in output
    assert "test song 1" in output
    assert "3:00" in output
    assert "2025-01-01" in output

def test_list_empty_db(test_db_path, capsys, monkeypatch):
    """Test listing an empty database"""
    # Create empty database
    init_db(test_db_path)
    
    # Mock get_db_path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.data.listdb.get_db_path', mock_db_path)
    
    # Call the function
    list_db_contents()
    
    # Check output
    captured = capsys.readouterr()
    output = captured.out.lower()
    assert "no albums found" in output
    assert "no songs found" in output
