import sqlite3
from pathlib import Path
import dataclasses
# build dataclasses for albums and songs using the sql ddl below


# ddl for albums table
album_table_ddl = """CREATE TABLE albums (
     album_id INTEGER PRIMARY KEY AUTOINCREMENT,
     name TEXT NOT NULL,
     release_date DATE NOT NULL,
     track_count INTEGER NOT NULL,
     spotify_url TEXT NOT NULL,
     image_large_uri TEXT NOT NULL,
     image_medium_uri TEXT NOT NULL,
     image_thumb_uri TEXT NOT NULL);"""



# ddl for songs table
song_table_ddl= """CREATE TABLE songs (
     song_id INTEGER PRIMARY KEY AUTOINCREMENT,
     album_id INTEGER NOT NULL,
     name TEXT NOT NULL,
     release_date DATE NOT NULL,
     track_number INTEGER,
     duration_ms INTEGER NOT NULL,
     duration TEXT NOT NULL,  -- stored as "M:SS" format
     spotify_url TEXT NOT NULL,
     image_large_uri TEXT NOT NULL,
     image_medium_uri TEXT NOT NULL,
     image_thumb_uri TEXT NOT NULL,
     FOREIGN KEY (album_id) REFERENCES albums(album_id));"""

@dataclasses.dataclass
class Album:
    album_id: str
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
    albums: list[Album]
    songs: list[Song]

@dataclasses.dataclass
class Artist:
    name: str
    discography: Discography
    songs: list[Song]
    albums: list[Album]

def get_db_path():
    """Get the path to the database file"""
    # Get the path to artistrack/data directory
    data_dir = Path(__file__).parent
    return data_dir / 'artistrack.db'

def recreate_db(db_path=None):
    """Drop and recreate the database and all tables"""
    if db_path is None:
        db_path = get_db_path()
    
    # Remove existing database if it exists
    if db_path.exists():
        db_path.unlink()
    
    # Create new database and tables
    init_db(db_path)
    print(f"Database recreated at {db_path}")

def init_db(db_path=None):
    """Initialize the SQLite database and create tables if they don't exist"""
    if db_path is None:
        db_path = get_db_path()
    
    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create albums table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS albums (
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
            image_thumb_uri TEXT NOT NULL
        )
    ''')
    
    # Create songs table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            song_id TEXT PRIMARY KEY,
            album_id TEXT,
            name TEXT NOT NULL,
            release_date TEXT NOT NULL,
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
            FOREIGN KEY (album_id) REFERENCES albums(album_id)
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
