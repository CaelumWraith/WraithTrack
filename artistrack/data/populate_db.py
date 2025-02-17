import sqlite3
from pathlib import Path
from datetime import datetime
from wraithtrack import get_all_artist_albums, get_album_tracks

def format_duration(duration_ms):
    """Convert duration in milliseconds to M:SS format"""
    total_seconds = int(duration_ms / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def populate_db():
    """Populate the database with albums and all songs (both album tracks and singles)"""
    
    db_path = Path('data') / 'wraith.db'
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Truncate existing tables
        print("Truncating existing tables...")
        cursor.execute("DELETE FROM songs")
        cursor.execute("DELETE FROM albums")
        conn.commit()
        
        # Get all albums data from Spotify
        print("Fetching albums data from Spotify...")
        all_albums = get_all_artist_albums()
        
        albums_count = 0
        album_tracks_count = 0
        singles_count = 0
        
        # First, process full albums and their tracks
        album_track_ids = set()  # Keep track of all album track IDs
        
        for item in all_albums:
            if item['album_type'] == 'album':
                # Insert album
                album_data = (
                    item['id'],
                    item['name'],
                    item['release_date'],
                    item['external_urls']['spotify'],
                    item['uri'],
                    item['total_tracks'],
                    'album',
                    item['images'][0]['url'],
                    item['images'][1]['url'],
                    item['images'][2]['url']
                )
                
                cursor.execute('''
                    INSERT INTO albums (
                        album_id, name, release_date, spotify_url, spotify_uri,
                        track_count, album_type, image_large_uri, image_medium_uri, image_thumb_uri
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', album_data)
                
                albums_count += 1
                print(f"\nAdded album: {item['name']}")
                
                # Get and insert album tracks
                tracks = get_album_tracks(item['id'])
                for track in tracks:
                    album_track_ids.add(track['id'])  # Add track ID to set
                    track_data = (
                        track['id'],
                        item['id'],  # album_id
                        track['name'],
                        item['release_date'],
                        track['track_number'],
                        track['duration_ms'],
                        format_duration(track['duration_ms']),
                        track['external_urls']['spotify'],
                        track['uri'],
                        False,  # is_single
                        item['images'][0]['url'],
                        item['images'][1]['url'],
                        item['images'][2]['url']
                    )
                    
                    cursor.execute('''
                        INSERT INTO songs (
                            song_id, album_id, name, release_date, track_number,
                            duration_ms, duration, spotify_url, spotify_uri, is_single,
                            image_large_uri, image_medium_uri, image_thumb_uri
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', track_data)
                    
                    album_tracks_count += 1
                    print(f"  Added track: {track['name']}")
        
        # Then, process singles (only if they're not already part of an album)
        for item in all_albums:
            if item['album_type'] == 'single':
                # Get the track data for the single
                tracks = get_album_tracks(item['id'])
                for track in tracks:
                    if track['id'] not in album_track_ids:  # Only add if not already in an album
                        single_data = (
                            track['id'],
                            None,  # album_id
                            track['name'],
                            item['release_date'],
                            None,  # track_number
                            track['duration_ms'],
                            format_duration(track['duration_ms']),
                            track['external_urls']['spotify'],
                            track['uri'],
                            True,  # is_single
                            item['images'][0]['url'],
                            item['images'][1]['url'],
                            item['images'][2]['url']
                        )
                        
                        cursor.execute('''
                            INSERT INTO songs (
                                song_id, album_id, name, release_date, track_number,
                                duration_ms, duration, spotify_url, spotify_uri, is_single,
                                image_large_uri, image_medium_uri, image_thumb_uri
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', single_data)
                        
                        singles_count += 1
                        print(f"Added single: {track['name']}")
                    else:
                        print(f"Skipping single {track['name']} (already in album)")
        
        # Commit all changes
        conn.commit()
        print(f"\nDatabase populated successfully:")
        print(f"Albums: {albums_count}")
        print(f"Album Tracks: {album_tracks_count}")
        print(f"Singles: {singles_count}")
        
        # Verify counts
        cursor.execute("SELECT COUNT(*) FROM albums")
        db_albums_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM songs WHERE is_single = 0")
        db_tracks_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM songs WHERE is_single = 1")
        db_singles_count = cursor.fetchone()[0]
        
        print("\nDatabase counts:")
        print(f"Albums in DB: {db_albums_count}")
        print(f"Album tracks in DB: {db_tracks_count}")
        print(f"Singles in DB: {db_singles_count}")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        print(f"Error details: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    populate_db() 