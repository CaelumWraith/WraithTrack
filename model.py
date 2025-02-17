import sqlite3
from pathlib import Path

def init_db():
    """Initialize the SQLite database and create tables if they don't exist"""
    
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Connect to SQLite database (creates it if it doesn't exist)
    db_path = data_dir / 'wraith.db'
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
            track_count INTEGER NOT NULL,
            album_type TEXT NOT NULL CHECK (album_type = 'album'),
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
