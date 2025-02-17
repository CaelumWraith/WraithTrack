import json
import sqlite3
from pathlib import Path
from datetime import datetime

def get_data_directory():
    """Get the data directory path"""
    return Path('data')

def get_current_date_string():
    """Get current date as string"""
    return datetime.now().strftime('%Y-%m-%d')

def format_duration(duration_ms):
    """Convert duration in milliseconds to M:SS format"""
    total_seconds = int(duration_ms / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def populate_singles():
    """Populate singles into the songs table"""
    
    data_dir = get_data_directory()
    current_date = get_current_date_string()
    db_path = data_dir / 'wraith.db'
    
    # Load artist albums data
    albums_file = data_dir / f"{current_date}__artist_albums.json"
    with open(albums_file, 'r') as f:
        albums_data = json.load(f)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    singles_count = 0
    
    try:
        # Process only singles from artist albums
        for item in albums_data['items']:
            if item['album_type'] == 'single':
                # For singles, use the album data directly
                single_data = (
                    item['id'],  # Use album ID as song ID for singles
                    None,  # album_id
                    item['name'],
                    item['release_date'],
                    None,  # track_number
                    0,  # duration_ms (will update with track data)
                    "0:00",  # duration (will update with track data)
                    item['external_urls']['spotify'],
                    item['uri'],
                    True,  # is_single
                    item['images'][0]['url'],  # large
                    item['images'][1]['url'],  # medium
                    item['images'][2]['url']   # thumb
                )
                
                cursor.execute('''
                    INSERT OR REPLACE INTO songs (
                        song_id, album_id, name, release_date, track_number,
                        duration_ms, duration, spotify_url, spotify_uri, is_single,
                        image_large_uri, image_medium_uri, image_thumb_uri
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', single_data)
                
                singles_count += 1
                print(f"Added single: {item['name']} ({item['release_date']})")
        
        # Commit all changes
        conn.commit()
        print(f"\nDatabase populated with {singles_count} singles successfully")
        
    except Exception as e:
        print(f"Error populating singles: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    populate_singles() 