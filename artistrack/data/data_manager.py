import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .model import Album, Song, Artist, Discography, init_db, get_db_path

class DataManager:
    def __init__(self):
        self.db_path = get_db_path()
        if not self.db_path.exists():
            init_db()
        
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
        
    def get_data_directory(self) -> Path:
        """Get the data directory path"""
        return self.db_path.parent
        
    def save_album(self, album_data: dict) -> Album:
        """Save album data to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Extract album data
        album = Album(
            album_id=album_data['id'],
            name=album_data['name'],
            release_date=album_data['release_date'],
            track_count=album_data['total_tracks'],
            spotify_url=album_data['external_urls']['spotify'],
            spotify_uri=album_data['uri'],
            album_type=album_data['album_type'],
            image_large_uri=album_data['images'][0]['url'],
            image_medium_uri=album_data['images'][1]['url'],
            image_thumb_uri=album_data['images'][2]['url']
        )
        
        # Insert album data
        cursor.execute('''
            INSERT OR REPLACE INTO albums (
                album_id, name, release_date, track_count, spotify_url,
                spotify_uri, album_type, image_large_uri, image_medium_uri,
                image_thumb_uri
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            album.album_id, album.name, album.release_date, album.track_count,
            album.spotify_url, album.spotify_uri, album.album_type,
            album.image_large_uri, album.image_medium_uri, album.image_thumb_uri
        ))
        
        conn.commit()
        conn.close()
        return album
        
    def save_song(self, song_data: dict, album_id: Optional[str] = None) -> Song:
        """Save song data to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Format duration
        duration_ms = song_data['duration_ms']
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        duration = f"{minutes}:{seconds:02d}"
        
        # Create song object
        song = Song(
            song_id=song_data['id'],
            album_id=album_id,
            name=song_data['name'],
            release_date=song_data.get('release_date', ''),  # May be None for album tracks
            track_number=song_data.get('track_number'),
            duration_ms=duration_ms,
            duration=duration,
            spotify_url=song_data['external_urls']['spotify'],
            spotify_uri=song_data['uri'],
            is_single=album_id is None,  # True if not part of an album
            image_large_uri=song_data['images'][0]['url'] if 'images' in song_data else '',
            image_medium_uri=song_data['images'][1]['url'] if 'images' in song_data else '',
            image_thumb_uri=song_data['images'][2]['url'] if 'images' in song_data else ''
        )
        
        # Insert song data
        cursor.execute('''
            INSERT OR REPLACE INTO songs (
                song_id, album_id, name, release_date, track_number,
                duration_ms, duration, spotify_url, spotify_uri, is_single,
                image_large_uri, image_medium_uri, image_thumb_uri
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            song.song_id, song.album_id, song.name, song.release_date,
            song.track_number, song.duration_ms, song.duration,
            song.spotify_url, song.spotify_uri, song.is_single,
            song.image_large_uri, song.image_medium_uri, song.image_thumb_uri
        ))
        
        conn.commit()
        conn.close()
        return song
        
    def get_artist_discography(self) -> Discography:
        """Get all albums and songs for the artist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all albums
        cursor.execute('SELECT * FROM albums ORDER BY release_date DESC')
        albums = [Album(*row) for row in cursor.fetchall()]
        
        # Get all songs
        cursor.execute('SELECT * FROM songs ORDER BY release_date DESC')
        songs = [Song(*row) for row in cursor.fetchall()]
        
        conn.close()
        return Discography(albums=albums, songs=songs)
        
    def get_song_by_title(self, title: str) -> Optional[Song]:
        """Get a song by its title"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM songs WHERE LOWER(name) = LOWER(?)', (title,))
        row = cursor.fetchone()
        
        conn.close()
        return Song(*row) if row else None
        
    def cleanup_old_files(self):
        """Remove old JSON files from the data directory"""
        data_dir = self.get_data_directory()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get all json files in the data directory
        for file in data_dir.glob("*.json"):
            # If the file doesn't start with today's date, delete it
            if not file.name.startswith(current_date):
                print(f"Removing old file: {file.name}")
                file.unlink()
