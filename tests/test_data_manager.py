import pytest
from pathlib import Path
from artistrack.data.data_manager import DataManager
from artistrack.data.model import Album, Song, Discography, init_db
from datetime import datetime
import sqlite3

@pytest.fixture
def mock_spotify_response():
    return {
        'id': 'test_album_id',
        'name': 'Test Album',
        'release_date': '2025-01-01',
        'total_tracks': 12,
        'external_urls': {'spotify': 'https://spotify/album'},
        'uri': 'spotify:album:test',
        'album_type': 'album',
        'artists': [{'id': 'test_artist_id', 'name': 'Test Artist'}],
        'images': [
            {'url': 'https://img/large'},
            {'url': 'https://img/medium'},
            {'url': 'https://img/thumb'}
        ]
    }

@pytest.fixture
def mock_track_response():
    return {
        'id': 'test_track_id',
        'name': 'Test Track',
        'release_date': '2025-01-01',
        'track_number': 1,
        'duration_ms': 180000,
        'external_urls': {'spotify': 'https://spotify/track'},
        'uri': 'spotify:track:test',
        'artists': [{'id': 'test_artist_id', 'name': 'Test Artist'}],
        'images': [
            {'url': 'https://img/large'},
            {'url': 'https://img/medium'},
            {'url': 'https://img/thumb'}
        ]
    }

def test_save_album(test_db_path, mock_spotify_response):
    """Test saving an album to the database"""
    data_manager = DataManager()
    data_manager.get_db_path = lambda: test_db_path
    
    # Save album
    album = data_manager.save_album(mock_spotify_response)
    
    # Verify album data
    assert isinstance(album, Album)
    assert album.album_id == mock_spotify_response["id"]
    assert album.artist_id == mock_spotify_response["artists"][0]["id"]
    assert album.name == mock_spotify_response["name"]
    assert album.spotify_uri == mock_spotify_response["uri"]
    assert album.qr_code_url == f"https://scannables.scdn.co/uri/plain/png/ffffff/black/640/{mock_spotify_response['uri']}"

def test_save_song(test_db_path, mock_track_response):
    """Test saving a song to the database"""
    data_manager = DataManager()
    data_manager.get_db_path = lambda: test_db_path
    
    # Save song
    song = data_manager.save_song(mock_track_response, "test_album_id")
    
    # Verify song data
    assert isinstance(song, Song)
    assert song.song_id == mock_track_response["id"]
    assert song.artist_id == mock_track_response["artists"][0]["id"]
    assert song.name == mock_track_response["name"]
    assert song.spotify_uri == mock_track_response["uri"]
    assert song.qr_code_url == f"https://scannables.scdn.co/uri/plain/png/ffffff/black/640/{mock_track_response['uri']}"
    assert song.album_id == "test_album_id"
    assert not song.is_single

def test_save_single(test_db_path, mock_track_response):
    """Test saving a song as a single"""
    data_manager = DataManager()
    data_manager.get_db_path = lambda: test_db_path
    
    # Save song without album_id
    song = data_manager.save_song(mock_track_response)
    
    # Verify song data
    assert isinstance(song, Song)
    assert song.song_id == mock_track_response["id"]
    assert song.artist_id == mock_track_response["artists"][0]["id"]
    assert song.album_id is None
    assert song.is_single

def test_get_artist_discography(test_db_path, mock_spotify_response, mock_track_response, monkeypatch):
    """Test getting artist discography"""
    # Create a fresh database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Mock get_db_path for both DataManager and init_db
    monkeypatch.setattr('artistrack.data.model.get_db_path', lambda: test_db_path)
    
    # Initialize database
    init_db()
    
    # Create data manager after database is initialized
    data_manager = DataManager()
    data_manager.db_path = test_db_path  # Override path to avoid init_db
    
    # Save test data
    album = data_manager.save_album(mock_spotify_response)
    
    # Create track responses
    track1_response = mock_track_response.copy()
    track1_response.update({
        'id': 'track1',
        'name': 'Test Track 1',
        'release_date': '2025-01-01',
        'track_number': 1,
        'duration_ms': 180000,
        'external_urls': {'spotify': 'https://spotify/track1'},
        'uri': 'spotify:track:1',
        'images': [
            {'url': 'https://img/large1'},
            {'url': 'https://img/medium1'},
            {'url': 'https://img/thumb1'}
        ]
    })
    
    track2_response = mock_track_response.copy()
    track2_response.update({
        'id': 'track2',
        'name': 'Test Track 2',
        'release_date': '2025-02-01',
        'track_number': None,
        'duration_ms': 240000,
        'external_urls': {'spotify': 'https://spotify/track2'},
        'uri': 'spotify:track:2',
        'images': [
            {'url': 'https://img/large2'},
            {'url': 'https://img/medium2'},
            {'url': 'https://img/thumb2'}
        ]
    })
    
    # Save tracks
    song1 = data_manager.save_song(track1_response, album.album_id)
    song2 = data_manager.save_song(track2_response)  # Save as single
    
    # Get discography
    discography = data_manager.get_artist_discography()
    
    # Verify discography
    assert isinstance(discography, Discography)
    assert len(discography.albums) == 1, f"Expected 1 album, got {len(discography.albums)}"
    assert len(discography.songs) == 2, f"Expected 2 songs, got {len(discography.songs)}"
    assert discography.albums[0].album_id == album.album_id
    assert any(s.song_id == 'track1' for s in discography.songs)
    assert any(s.song_id == 'track2' for s in discography.songs)

def test_get_song_by_title(test_db_path, mock_track_response):
    """Test getting a song by title"""
    data_manager = DataManager()
    data_manager.get_db_path = lambda: test_db_path
    
    # Create a fresh database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize database
    conn = data_manager.get_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            song_id TEXT PRIMARY KEY,
            album_id TEXT,
            artist_id TEXT NOT NULL,
            name TEXT NOT NULL,
            release_date TEXT NOT NULL,
            track_number INTEGER,
            duration_ms INTEGER NOT NULL,
            duration TEXT NOT NULL,
            spotify_url TEXT NOT NULL,
            spotify_uri TEXT NOT NULL,
            qr_code_url TEXT NOT NULL,
            is_single BOOLEAN NOT NULL,
            image_large_uri TEXT NOT NULL,
            image_medium_uri TEXT NOT NULL,
            image_thumb_uri TEXT NOT NULL,
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Create test song data
    test_song = mock_track_response.copy()
    test_song['id'] = 'test_song'
    test_song['name'] = 'Test Song Title'
    
    # Save test song
    saved_song = data_manager.save_song(test_song)
    
    # Get song by title
    found_song = data_manager.get_song_by_title('Test Song Title')
    
    # Verify song data
    assert found_song is not None
    assert found_song.song_id == 'test_song'
    assert found_song.name == 'Test Song Title'
    assert found_song.artist_id == 'test_artist_id'
    
    # Test case insensitive search
    found_song = data_manager.get_song_by_title('TEST SONG TITLE')
    assert found_song is not None
    assert found_song.song_id == 'test_song'
    
    # Test non-existent song
    not_found = data_manager.get_song_by_title("Non-existent Song")
    assert not_found is None

def test_cleanup_old_files(test_db_path, tmp_path, monkeypatch):
    """Test cleaning up old files"""
    data_manager = DataManager()
    data_manager.get_db_path = lambda: test_db_path
    
    # Create test files
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Mock get_data_directory
    monkeypatch.setattr(data_manager, 'get_data_directory', lambda: data_dir)
    
    # Create test files with different dates
    current_date = datetime.now().strftime("%Y-%m-%d")
    (data_dir / f"{current_date}_current.json").touch()
    (data_dir / "2024-01-01_old.json").touch()
    (data_dir / "not_a_date.json").touch()
    (data_dir / "text.txt").touch()  # Non-JSON file
    
    # Run cleanup
    data_manager.cleanup_old_files()
    
    # Verify files
    remaining_files = list(data_dir.glob("*"))
    assert len(remaining_files) == 2  # Current JSON and non-JSON file
    assert (data_dir / f"{current_date}_current.json").exists()
    assert (data_dir / "text.txt").exists()
    assert not (data_dir / "2024-01-01_old.json").exists()
    assert not (data_dir / "not_a_date.json").exists()

def test_database_initialization(tmp_path):
    """Test database initialization"""
    # Create test database path
    test_db_path = tmp_path / "test.db"
    
    # Initialize database
    init_db(test_db_path)
    
    # Verify database was created
    assert test_db_path.exists()
    
    # Connect to database and check tables
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Check artists table
    cursor.execute("PRAGMA table_info(artists)")
    artist_columns = [col[1] for col in cursor.fetchall()]
    assert all(col in artist_columns for col in [
        "artist_id", "name", "spotify_url", "image_large_uri",
        "image_medium_uri", "image_thumb_uri", "followers"
    ])
    
    # Check albums table
    cursor.execute("PRAGMA table_info(albums)")
    album_columns = [col[1] for col in cursor.fetchall()]
    assert all(col in album_columns for col in [
        "album_id", "artist_id", "name", "release_date", "spotify_url",
        "spotify_uri", "qr_code_url", "track_count", "album_type",
        "image_large_uri", "image_medium_uri", "image_thumb_uri"
    ])
    
    # Check songs table
    cursor.execute("PRAGMA table_info(songs)")
    song_columns = [col[1] for col in cursor.fetchall()]
    assert all(col in song_columns for col in [
        "song_id", "album_id", "artist_id", "name", "release_date",
        "track_number", "duration_ms", "duration", "spotify_url",
        "spotify_uri", "qr_code_url", "is_single", "image_large_uri",
        "image_medium_uri", "image_thumb_uri"
    ])
    
    # Check foreign key constraints
    cursor.execute("PRAGMA foreign_key_list(albums)")
    album_fks = cursor.fetchall()
    assert any(fk[3] == "artist_id" and fk[2] == "artists" for fk in album_fks)
    
    cursor.execute("PRAGMA foreign_key_list(songs)")
    song_fks = cursor.fetchall()
    assert any(fk[3] == "album_id" and fk[2] == "albums" for fk in song_fks)
    assert any(fk[3] == "artist_id" and fk[2] == "artists" for fk in song_fks)
    
    conn.close()

def test_database_connection_error(tmp_path, monkeypatch):
    """Test handling of database connection errors"""
    # Create test database
    db_path = tmp_path / "test.db"
    
    # Create empty database with tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE albums (
            album_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            release_date TEXT NOT NULL,
            spotify_url TEXT NOT NULL,
            spotify_uri TEXT NOT NULL,
            qr_code_url TEXT NOT NULL,
            track_count INTEGER NOT NULL,
            album_type TEXT NOT NULL,
            image_large_uri TEXT NOT NULL,
            image_medium_uri TEXT NOT NULL,
            image_thumb_uri TEXT NOT NULL,
            artist_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
    # Make database read-only
    db_path.chmod(0o444)
    
    # Mock get_db_path
    monkeypatch.setattr('artistrack.data.model.get_db_path', lambda: db_path)
    
    # Create data manager
    data_manager = DataManager()
    data_manager.db_path = db_path  # Override path to avoid init_db
    
    # Verify connection error is handled
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        data_manager.save_album({
            'id': 'test',
            'name': 'Test Album',
            'release_date': '2025-01-01',
            'total_tracks': 1,
            'external_urls': {'spotify': 'https://spotify/test'},
            'uri': 'spotify:album:test',
            'album_type': 'album',
            'images': [
                {'url': 'https://img/large'},
                {'url': 'https://img/medium'},
                {'url': 'https://img/thumb'}
            ],
            'artists': [{'id': 'test_artist_id', 'name': 'Test Artist'}]
        })
    
    assert "readonly database" in str(exc_info.value).lower()
    
    # Cleanup: restore permissions
    db_path.chmod(0o666)

@pytest.mark.skip("Skipping test_database_query_error")
def test_database_query_error(test_db_path, monkeypatch):
    """Test handling of database query errors"""
    # Create test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Create empty database with wrong schema
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
    # Mock get_db_path
    monkeypatch.setattr('artistrack.data.model.get_db_path', lambda: test_db_path)
    
    # Create data manager
    data_manager = DataManager()
    data_manager.db_path = test_db_path  # Override path to avoid init_db
    
    # Try to save a song (should fail since table has wrong schema)
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        data_manager.save_song({
            'id': 'test',
            'name': 'Test Song',
            'release_date': '2025-01-01',
            'duration_ms': 180000,
            'external_urls': {'spotify': 'https://spotify/test'},
            'uri': 'spotify:track:test',
            'images': [
                {'url': 'https://img/large'},
                {'url': 'https://img/medium'},
                {'url': 'https://img/thumb'}
            ],
            'artists': [{'id': 'test_artist_id', 'name': 'Test Artist'}]
        })
    
    assert "no such column" in str(exc_info.value).lower()

def test_database_initialization_error(tmp_path, monkeypatch):
    """Test handling of database initialization errors"""
    # Create test database
    db_path = tmp_path / "test.db"
    
    # Create empty database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    # Make database read-only
    db_path.chmod(0o444)
    
    # Mock get_db_path
    monkeypatch.setattr('artistrack.data.model.get_db_path', lambda: db_path)
    
    # Verify initialization error is handled
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        init_db()
    
    assert "readonly database" in str(exc_info.value).lower()
    
    # Cleanup: restore permissions
    db_path.chmod(0o666)
