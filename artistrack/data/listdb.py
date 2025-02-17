import sqlite3
from pathlib import Path
from model import get_db_path

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
        cursor.execute('''
            SELECT * FROM albums 
            ORDER BY release_date DESC
        ''')
        
        for row in cursor.fetchall():
            print(f"Album: {row['name']}")
            print(f"Release Date: {row['release_date']}")
            print(f"Track Count: {row['track_count']}")
            print(f"Spotify URL: {row['spotify_url']}")
            print("-" * 80)
        
        print("\n=== SONGS ===")
        print("-" * 80)
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
        
        for row in cursor.fetchall():
            print(f"Track: {row['name']}")
            print(f"Release Date: {row['release_date']}")
            print(f"Duration: {row['duration']}")
            print(f"{'Single' if row['is_single'] else 'Album Track'} - Album: {row['album_name']}")
            print(f"Spotify URL: {row['spotify_url']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error listing database contents: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    list_db_contents()
