import sqlite3
from pathlib import Path
from artistrack.data.model import get_db_path

def list_db_contents():
    """List all rows from both albums and songs tables"""
    
    # Connect to database
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    # Set row factory to get dictionary-like results
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print("\n=== ALBUMS ===")
        print("-" * 80)
        
        # Get all albums
        cursor.execute('''
            SELECT * FROM albums 
            ORDER BY release_date DESC
        ''')
        albums = cursor.fetchall()
        
        if not albums:
            print("No albums found")
        else:
            for album in albums:
                print(f"Album: {album['name']}")
                print(f"Release Date: {album['release_date']}")
                print(f"Track Count: {album['track_count']}")
                print(f"Spotify URL: {album['spotify_url']}")
                print("-" * 80)
        
        print("\n=== SONGS ===")
        print("-" * 80)
        
        # Get all songs
        cursor.execute('''
            SELECT 
                s.*,
                CASE 
                    WHEN s.is_single = 1 THEN 'Single'
                    ELSE a.name 
                END as album_name
            FROM songs s
            LEFT JOIN albums a ON s.album_id = a.album_id
            ORDER BY s.release_date DESC, s.track_number
        ''')
        songs = cursor.fetchall()
        
        if not songs:
            print("No songs found")
        else:
            for song in songs:
                print(f"Track: {song['name']}")
                print(f"Release Date: {song['release_date']}")
                print(f"Duration: {song['duration']}")
                print(f"{'Single' if song['is_single'] else 'Album Track'} - Album: {song['album_name']}")
                print(f"Spotify URL: {song['spotify_url']}")
                print("-" * 80)
            
    except Exception as e:
        print(f"Error listing database contents: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    list_db_contents()
