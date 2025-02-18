import sqlite3
from pathlib import Path
import dataclasses
from datetime import datetime, timedelta
import random

# ddl for artists table
artist_table_ddl = """CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spotify_url TEXT NOT NULL,
    spotify_uri TEXT NOT NULL,
    image_large_uri TEXT,
    image_medium_uri TEXT,
    image_thumb_uri TEXT
);"""

# ddl for albums table
album_table_ddl = """CREATE TABLE albums (
    album_id TEXT PRIMARY KEY,
    artist_id TEXT NOT NULL,
    name TEXT NOT NULL,
    release_date DATE NOT NULL,
    track_count INTEGER NOT NULL,
    spotify_url TEXT NOT NULL,
    spotify_uri TEXT NOT NULL,
    qr_code_url TEXT NOT NULL,
    album_type TEXT NOT NULL,
    image_large_uri TEXT NOT NULL,
    image_medium_uri TEXT NOT NULL,
    image_thumb_uri TEXT NOT NULL,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);"""

# ddl for songs table
song_table_ddl = """CREATE TABLE songs (
    song_id TEXT PRIMARY KEY,
    artist_id TEXT NOT NULL,
    album_id TEXT,
    name TEXT NOT NULL,
    release_date DATE NOT NULL,
    track_number INTEGER,
    duration_ms INTEGER NOT NULL,
    duration TEXT NOT NULL,  -- stored as "M:SS" format
    spotify_url TEXT NOT NULL,
    spotify_uri TEXT NOT NULL,
    qr_code_url TEXT NOT NULL,
    is_single BOOLEAN NOT NULL,
    image_large_uri TEXT NOT NULL,
    image_medium_uri TEXT NOT NULL,
    image_thumb_uri TEXT NOT NULL,
    FOREIGN KEY (album_id) REFERENCES albums(album_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);"""

@dataclasses.dataclass
class Artist:
    artist_id: str
    name: str
    spotify_url: str
    spotify_uri: str
    image_large_uri: str
    image_medium_uri: str
    image_thumb_uri: str

@dataclasses.dataclass
class Album:
    album_id: str
    artist_id: str
    name: str
    release_date: str
    track_count: int
    spotify_url: str
    spotify_uri: str
    qr_code_url: str
    album_type: str
    image_large_uri: str
    image_medium_uri: str
    image_thumb_uri: str

@dataclasses.dataclass
class Song:
    song_id: str
    artist_id: str
    album_id: str
    name: str
    release_date: str
    track_number: int
    duration_ms: int
    duration: str
    spotify_url: str
    spotify_uri: str
    qr_code_url: str
    is_single: bool
    image_large_uri: str
    image_medium_uri: str
    image_thumb_uri: str

@dataclasses.dataclass
class Discography:
    artist: Artist
    albums: list[Album]
    songs: list[Song]

def get_db_path():
    """Get the path to the database file"""
    # Get the path to artistrack/data directory
    data_dir = Path(__file__).parent
    return data_dir / 'artistrack.db'

def init_db(db_path=None):
    """Initialize the SQLite database and create tables if they don't exist.
    
    Args:
        db_path: Optional path to database file. If None, uses default path.
    """
    if db_path is None:
        db_path = get_db_path()
    
    # Create parent directory if it doesn't exist
    if isinstance(db_path, str):
        db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            spotify_url TEXT NOT NULL,
            spotify_uri TEXT NOT NULL,
            image_large_uri TEXT,
            image_medium_uri TEXT,
            image_thumb_uri TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            album_id TEXT PRIMARY KEY,
            artist_id TEXT NOT NULL,
            name TEXT NOT NULL,
            release_date DATE NOT NULL,
            track_count INTEGER NOT NULL,
            spotify_url TEXT NOT NULL,
            spotify_uri TEXT NOT NULL,
            qr_code_url TEXT NOT NULL,
            album_type TEXT NOT NULL,
            image_large_uri TEXT NOT NULL,
            image_medium_uri TEXT NOT NULL,
            image_thumb_uri TEXT NOT NULL,
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            song_id TEXT PRIMARY KEY,
            artist_id TEXT NOT NULL,
            album_id TEXT,
            name TEXT NOT NULL,
            release_date DATE NOT NULL,
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
            FOREIGN KEY (album_id) REFERENCES albums(album_id),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)
    
    conn.commit()
    conn.close()

def recreate_db(db_path=None):
    """Drop and recreate the database and all tables.
    
    Args:
        db_path: Optional path to database file. If None, uses default path.
    """
    if db_path is None:
        db_path = get_db_path()
    
    # Delete existing database file
    if isinstance(db_path, str):
        db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    
    # Create new database
    init_db(db_path)

def init_or_update_db():
    """Initialize or update the database schema"""
    db_path = get_db_path()
    
    # Check if database exists
    if not db_path.exists():
        init_db()
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    # Create missing tables
    if 'artists' not in tables:
        cursor.execute(artist_table_ddl)
    if 'albums' not in tables:
        cursor.execute(album_table_ddl)
    if 'songs' not in tables:
        cursor.execute(song_table_ddl)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
