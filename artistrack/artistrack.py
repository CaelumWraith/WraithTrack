import json
from datetime import datetime
import os
from artistrack.data.model import init_db, recreate_db
from artistrack.discotech.spotify_client import SpotifyClient
from artistrack.data.data_manager import DataManager
from artistrack.discotech.generate_discography import generate_discography
from artistrack.storybuilder.instastory import create_story
import requests
import sys
from pathlib import Path
import argparse

# Token management
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
bearer_token = None
bearer_token_expires = None

def populate_artist_data(verbose: bool = False):
    """Populate the database with artist data"""
    try:
        spotify = SpotifyClient(verbose=verbose)
        data_manager = DataManager()
        
        # Get artist data
        print("Fetching artist data...")
        artist_data = spotify.get_artist_data()
        
        # Get all albums
        print("Fetching artist albums...")
        albums = spotify.get_all_artist_albums()
        
        # Process each album
        print(f"Processing {len(albums)} albums...")
        for i, album_data in enumerate(albums, 1):
            # Save album
            album = data_manager.save_album(album_data)
            print(f"[{i}/{len(albums)}] Saved album: {album.name}")
            
            # Get and save all tracks for this album
            tracks = spotify.get_album_tracks(album_data['id'])
            for track_data in tracks:
                # Add album images to track data since they're not included in track response
                track_data['images'] = album_data['images']
                track_data['release_date'] = album_data['release_date']
                data_manager.save_song(track_data, album.album_id)
            print(f"  - Saved {len(tracks)} tracks")
        
        print("\nDatabase population completed successfully!")
        
    except Exception as e:
        print(f"\nError populating database: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Artistrack - Track artist discography')
    parser.add_argument('--newdb', action='store_true', help='Recreate the database')
    parser.add_argument('--verbose', action='store_true', help='Show detailed API responses and data')
    parser.add_argument('--build-discography', action='store_true', help='Generate discography.html')
    parser.add_argument('--generate-story', help='Generate story image for a song')
    parser.add_argument('--output-path', help='Output path for generated story (default: current directory)')
    parser.add_argument('--refresh-data', action='store_true', help='Fetch fresh data from Spotify API')
    args = parser.parse_args()
    
    # Recreate database if requested
    if args.newdb:
        recreate_db()
    
    # Populate artist data if refresh requested
    if args.refresh_data:
        populate_artist_data(verbose=args.verbose)
    
    # Generate discography if requested
    if args.build_discography:
        generate_discography()
    
    # Generate story if requested
    if args.generate_story:
        create_story(args.generate_story, args.output_path)

# pragma: no cover
if __name__ == "__main__":
    main()
