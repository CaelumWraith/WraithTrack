import pytest
from pathlib import Path
import sqlite3
from bs4 import BeautifulSoup
from artistrack.discotech.generate_discography import generate_discography
from artistrack.data.model import init_db

@pytest.fixture
def test_db_path(tmp_path):
    """Create a test database path"""
    return tmp_path / "test.db"

def test_generate_discography(test_db_path, tmp_path, monkeypatch):
    """Test generating discography HTML with sample data"""
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
    
    cursor.execute("""
        INSERT INTO songs (
            song_id, album_id, name, release_date, track_number, duration_ms,
            duration, spotify_url, spotify_uri, qr_code_url, is_single,
            image_large_uri, image_medium_uri, image_thumb_uri
        ) VALUES (
            'song2', NULL, 'Test Single', '2024-02-01', NULL, 240000,
            '4:00', 'http://spotify/song2', 'spotify:track:2', 'http://qr/song2',
            1, 'http://img/large2', 'http://img/medium2', 'http://img/thumb2'
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Mock get_db_path to return test path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.discotech.generate_discography.get_db_path', mock_db_path)
    
    # Generate discography
    output_path = generate_discography(tmp_path)
    
    # Verify output file exists
    assert output_path.exists()
    
    # Parse HTML and check content
    with open(output_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # Check album data
        assert 'Test Album' in soup.get_text()
        assert 'Test Song' in soup.get_text()
        assert '3:00' in soup.get_text()
        assert 'Test Single' in soup.get_text()
        assert '4:00' in soup.get_text()
        
        # Check links
        links = soup.find_all('a')
        assert any('spotify/album1' in link['href'] for link in links)
        assert any('spotify/song1' in link['href'] for link in links)
        assert any('qr/album1' in link['href'] for link in links)
        assert any('qr/song1' in link['href'] for link in links)
        assert any('spotify/song2' in link['href'] for link in links)
        assert any('qr/song2' in link['href'] for link in links)

def test_generate_empty_discography(test_db_path, tmp_path, monkeypatch):
    """Test generating discography HTML with empty database"""
    # Initialize empty test database
    init_db(test_db_path)
    
    # Mock get_db_path to return test path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.discotech.generate_discography.get_db_path', mock_db_path)
    
    # Generate discography
    output_path = generate_discography(tmp_path)
    
    # Verify output file exists
    assert output_path.exists()
    
    # Parse HTML and check content
    with open(output_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
        assert 'No albums found' in soup.get_text()
