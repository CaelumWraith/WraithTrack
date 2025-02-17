import pytest
from pathlib import Path
import sqlite3
from bs4 import BeautifulSoup
from artistrack.discotech.generate_discography import generate_discography
from artistrack.data.model import init_db

def test_generate_discography(test_db_path, tmp_path, monkeypatch):
    """Test generating discography HTML"""
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
    
    cursor.execute('''
        INSERT INTO songs (
            song_id, album_id, name, release_date, track_number,
            duration_ms, duration, spotify_url, spotify_uri, qr_code_url,
            is_single, image_large_uri, image_medium_uri, image_thumb_uri
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'song2', None, 'Test Single', '2025-02-01', None,
        240000, '4:00', 'https://spotify/song2', 'spotify:track:2',
        'https://qr/song2', True, 'https://img/large2', 'https://img/medium2',
        'https://img/thumb2'
    ))
    
    conn.commit()
    conn.close()
    
    # Mock get_db_path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.discotech.generate_discography.get_db_path', mock_db_path)
    
    # Set output path
    output_path = tmp_path / 'discography.html'
    
    def mock_path_join(self, other):
        if other == 'discography.html':
            return output_path
        return Path(str(self) + '/' + str(other))
    
    monkeypatch.setattr('pathlib.Path.__truediv__', mock_path_join)
    
    # Generate discography
    generate_discography()
    
    # Verify file was created
    assert output_path.exists()
    
    # Parse and verify HTML content
    with open(output_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # Check album
        album_row = soup.find('tr', class_='main-row')
        assert album_row is not None
        assert album_row.find('a', string='Test Album') is not None
        assert album_row.find('td', string='Album') is not None
        assert album_row.find('a', href='https://spotify/album1') is not None
        assert album_row.find('a', href='https://qr/album1') is not None
        
        # Check album track
        track_row = soup.find('tr', class_='track-row')
        assert track_row is not None
        assert track_row.find('a', string='Test Song 1') is not None
        assert track_row.find('td', class_='duration', string='3:00') is not None
        assert track_row.find('a', href='https://spotify/song1') is not None
        
        # Check single
        single_rows = soup.find_all('tr', class_='main-row')
        single_row = next((row for row in single_rows if row.find('td', string='Single')), None)
        assert single_row is not None
        assert single_row.find('a', string='Test Single') is not None
        assert single_row.find('td', class_='duration', string='4:00') is not None
        assert single_row.find('a', href='https://spotify/song2') is not None

def test_generate_empty_discography(test_db_path, tmp_path, monkeypatch):
    """Test generating discography HTML with no data"""
    # Create empty database
    init_db(test_db_path)
    
    # Mock get_db_path
    def mock_db_path():
        return test_db_path
    monkeypatch.setattr('artistrack.discotech.generate_discography.get_db_path', mock_db_path)
    
    # Set output path
    output_path = tmp_path / 'discography.html'
    
    def mock_path_join(self, other):
        if other == 'discography.html':
            return output_path
        return Path(str(self) + '/' + str(other))
    
    monkeypatch.setattr('pathlib.Path.__truediv__', mock_path_join)
    
    # Generate discography
    generate_discography()
    
    # Verify file was created
    assert output_path.exists()
    
    # Parse and verify HTML content
    with open(output_path) as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # Should have table headers but no data rows
        assert soup.find('table', class_='discography') is not None
        assert soup.find('th', string='Track') is not None
        assert soup.find('tr', class_='main-row') is None
        assert soup.find('tr', class_='track-row') is None
