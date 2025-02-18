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
    
    def save_artist(self, artist_data: dict) -> Artist:
        """Save artist data to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create artist object
        artist = Artist(
            artist_id=artist_data['id'],
            name=artist_data['name'],
            spotify_url=artist_data['external_urls']['spotify'],
            spotify_uri=artist_data['uri'],
            image_large_uri=artist_data['images'][0]['url'] if artist_data.get('images') else '',
            image_medium_uri=artist_data['images'][1]['url'] if artist_data.get('images') and len(artist_data['images']) > 1 else '',
            image_thumb_uri=artist_data['images'][2]['url'] if artist_data.get('images') and len(artist_data['images']) > 2 else ''
        )
        
        # Insert artist data
        cursor.execute('''
            INSERT OR REPLACE INTO artists (
                artist_id, name, spotify_url, spotify_uri,
                image_large_uri, image_medium_uri, image_thumb_uri
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            artist.artist_id, artist.name, artist.spotify_url,
            artist.spotify_uri, artist.image_large_uri,
            artist.image_medium_uri, artist.image_thumb_uri
        ))
        
        conn.commit()
        conn.close()
        return artist
        
    def save_album(self, album_data: dict, artist_id: str) -> Album:
        """Save album data to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Extract album data
        album = Album(
            album_id=album_data['id'],
            artist_id=artist_id,
            name=album_data['name'],
            release_date=album_data['release_date'],
            track_count=album_data['total_tracks'],
            spotify_url=album_data['external_urls']['spotify'],
            spotify_uri=album_data['uri'],
            qr_code_url=f"https://scannables.scdn.co/uri/plain/png/ffffff/black/640/{album_data['uri']}",
            album_type=album_data['album_type'],
            image_large_uri=album_data['images'][0]['url'],
            image_medium_uri=album_data['images'][1]['url'],
            image_thumb_uri=album_data['images'][2]['url']
        )
        
        # Insert album data
        cursor.execute('''
            INSERT OR REPLACE INTO albums (
                album_id, artist_id, name, release_date, track_count,
                spotify_url, spotify_uri, qr_code_url, album_type,
                image_large_uri, image_medium_uri, image_thumb_uri
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            album.album_id, album.artist_id, album.name, album.release_date,
            album.track_count, album.spotify_url, album.spotify_uri,
            album.qr_code_url, album.album_type, album.image_large_uri,
            album.image_medium_uri, album.image_thumb_uri
        ))
        
        conn.commit()
        conn.close()
        return album
        
    def save_song(self, song_data: dict, artist_id: str, album_id: Optional[str] = None) -> Song:
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
            artist_id=artist_id,
            album_id=album_id,
            name=song_data['name'],
            release_date=song_data.get('release_date', ''),  # May be None for album tracks
            track_number=song_data.get('track_number'),
            duration_ms=duration_ms,
            duration=duration,
            spotify_url=song_data['external_urls']['spotify'],
            spotify_uri=song_data['uri'],
            qr_code_url=f"https://scannables.scdn.co/uri/plain/png/ffffff/black/640/{song_data['uri']}",
            is_single=album_id is None,  # True if not part of an album
            image_large_uri=song_data['images'][0]['url'] if 'images' in song_data else '',
            image_medium_uri=song_data['images'][1]['url'] if 'images' in song_data else '',
            image_thumb_uri=song_data['images'][2]['url'] if 'images' in song_data else ''
        )
        
        # Insert song data
        cursor.execute('''
            INSERT OR REPLACE INTO songs (
                song_id, artist_id, album_id, name, release_date,
                track_number, duration_ms, duration, spotify_url,
                spotify_uri, qr_code_url, is_single, image_large_uri,
                image_medium_uri, image_thumb_uri
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            song.song_id, song.artist_id, song.album_id, song.name,
            song.release_date, song.track_number, song.duration_ms,
            song.duration, song.spotify_url, song.spotify_uri,
            song.qr_code_url, song.is_single, song.image_large_uri,
            song.image_medium_uri, song.image_thumb_uri
        ))
        
        conn.commit()
        conn.close()
        return song
    
    def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get artist by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT artist_id, name, spotify_url, spotify_uri,
                   image_large_uri, image_medium_uri, image_thumb_uri
            FROM artists WHERE artist_id = ?
        ''', (artist_id,))
        
        row = cursor.fetchone()
        if row:
            artist = Artist(
                artist_id=row[0],
                name=row[1],
                spotify_url=row[2],
                spotify_uri=row[3],
                image_large_uri=row[4],
                image_medium_uri=row[5],
                image_thumb_uri=row[6]
            )
            return artist
        return None
    
    def get_artists(self) -> List[Artist]:
        """Get all artists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT artist_id, name, spotify_url, spotify_uri,
                   image_large_uri, image_medium_uri, image_thumb_uri
            FROM artists
        ''')
        
        artists = []
        for row in cursor.fetchall():
            artist = Artist(
                artist_id=row[0],
                name=row[1],
                spotify_url=row[2],
                spotify_uri=row[3],
                image_large_uri=row[4],
                image_medium_uri=row[5],
                image_thumb_uri=row[6]
            )
            artists.append(artist)
        
        conn.close()
        return artists
    
    def get_discography(self, artist_id: str) -> Optional[Discography]:
        """Get artist's complete discography"""
        artist = self.get_artist(artist_id)
        if not artist:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get albums
        cursor.execute('''
            SELECT album_id, artist_id, name, release_date, track_count,
                   spotify_url, spotify_uri, qr_code_url, album_type,
                   image_large_uri, image_medium_uri, image_thumb_uri
            FROM albums WHERE artist_id = ?
        ''', (artist_id,))
        
        albums = []
        for row in cursor.fetchall():
            album = Album(
                album_id=row[0],
                artist_id=row[1],
                name=row[2],
                release_date=row[3],
                track_count=row[4],
                spotify_url=row[5],
                spotify_uri=row[6],
                qr_code_url=row[7],
                album_type=row[8],
                image_large_uri=row[9],
                image_medium_uri=row[10],
                image_thumb_uri=row[11]
            )
            albums.append(album)
        
        # Get songs
        cursor.execute('''
            SELECT song_id, artist_id, album_id, name, release_date,
                   track_number, duration_ms, duration, spotify_url,
                   spotify_uri, qr_code_url, is_single, image_large_uri,
                   image_medium_uri, image_thumb_uri
            FROM songs WHERE artist_id = ?
        ''', (artist_id,))
        
        songs = []
        for row in cursor.fetchall():
            song = Song(
                song_id=row[0],
                artist_id=row[1],
                album_id=row[2],
                name=row[3],
                release_date=row[4],
                track_number=row[5],
                duration_ms=row[6],
                duration=row[7],
                spotify_url=row[8],
                spotify_uri=row[9],
                qr_code_url=row[10],
                is_single=row[11],
                image_large_uri=row[12],
                image_medium_uri=row[13],
                image_thumb_uri=row[14]
            )
            songs.append(song)
        
        conn.close()
        return Discography(artist=artist, albums=albums, songs=songs)
    
    def get_artist_discography(self) -> Discography:
        """Get all albums and songs for the artist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all albums
        cursor.execute('''
            SELECT 
                album_id, artist_id, name, release_date, track_count, spotify_url,
                spotify_uri, qr_code_url, album_type, image_large_uri,
                image_medium_uri, image_thumb_uri
            FROM albums 
            ORDER BY release_date DESC
        ''')
        albums = [Album(*row) for row in cursor.fetchall()]
        
        # Get all songs
        cursor.execute('''
            SELECT 
                song_id, artist_id, album_id, name, release_date,
                track_number, duration_ms, duration, spotify_url,
                spotify_uri, qr_code_url, is_single, image_large_uri,
                image_medium_uri, image_thumb_uri
            FROM songs 
            ORDER BY release_date DESC
        ''')
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
