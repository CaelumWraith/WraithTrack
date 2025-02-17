import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import argparse
from artistrack.artistrack import populate_artist_data, main
import runpy

@pytest.fixture
def mock_spotify_client(mocker):
    """Mock SpotifyClient"""
    mock_client = Mock()
    mock_client.get_artist_data.return_value = {"name": "Test Artist"}
    mock_client.get_all_artist_albums.return_value = [{
        "id": "album1",
        "name": "Test Album",
        "release_date": "2025-01-01",
        "total_tracks": 2,
        "external_urls": {"spotify": "https://spotify/album1"},
        "uri": "spotify:album:1",
        "album_type": "album",
        "images": [
            {"url": "https://img/large1"},
            {"url": "https://img/medium1"},
            {"url": "https://img/thumb1"}
        ]
    }]
    mock_client.get_album_tracks.return_value = [{
        "id": "track1",
        "name": "Test Track",
        "duration_ms": 180000,
        "track_number": 1,
        "external_urls": {"spotify": "https://spotify/track1"},
        "uri": "spotify:track:1",
        "images": [
            {"url": "https://img/large1"},
            {"url": "https://img/medium1"},
            {"url": "https://img/thumb1"}
        ]
    }]
    return mock_client

@pytest.fixture
def mock_data_manager(mocker):
    """Mock DataManager"""
    mock_manager = Mock()
    mock_album = Mock()
    mock_album.name = "Test Album"
    mock_manager.save_album.return_value = mock_album
    mock_manager.save_song.return_value = Mock(song_id="track1")
    return mock_manager

def test_populate_artist_data(mocker, mock_spotify_client, mock_data_manager, capsys):
    """Test populating artist data"""
    # Mock SpotifyClient and DataManager
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    
    # Call function
    populate_artist_data(verbose=True)
    
    # Verify API calls
    mock_spotify_client.get_artist_data.assert_called_once()
    mock_spotify_client.get_all_artist_albums.assert_called_once()
    mock_spotify_client.get_album_tracks.assert_called_once_with("album1")
    
    # Verify database saves
    mock_data_manager.save_album.assert_called_once()
    mock_data_manager.save_song.assert_called_once()
    
    # Verify output
    captured = capsys.readouterr()
    assert "Processing 1 albums..." in captured.out
    assert "Saved album: Test Album" in captured.out
    assert "Saved 1 tracks" in captured.out

def test_populate_artist_data_error(mocker, mock_spotify_client, mock_data_manager, capsys):
    """Test error handling in populate_artist_data"""
    # Make get_artist_data raise an error
    mock_spotify_client.get_artist_data.side_effect = Exception("API Error")
    
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    
    # Call function and verify it exits with error
    with pytest.raises(SystemExit) as exc_info:
        populate_artist_data(verbose=True)
    
    assert exc_info.value.code == 1
    
    # Verify error output
    captured = capsys.readouterr()
    assert "Error populating database: API Error" in captured.out

def test_main_refresh_data(mocker, mock_spotify_client, mock_data_manager, tmp_path):
    """Test main function with --refresh-data"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=True,
        verbose=True,
        newdb=False,
        build_discography=False,
        generate_story=None,
        output_path=None
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    mocker.patch('artistrack.artistrack.recreate_db')
    mocker.patch('artistrack.artistrack.generate_discography')
    mocker.patch('artistrack.artistrack.create_story')
    
    # Run main
    main()
    
    # Verify correct functions were called
    mock_spotify_client.get_artist_data.assert_called_once()
    mock_spotify_client.get_all_artist_albums.assert_called_once()

def test_main_generate_story(mocker, mock_spotify_client, mock_data_manager, tmp_path):
    """Test main function with --generate-story"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=False,
        verbose=False,
        newdb=False,
        build_discography=False,
        generate_story="Test Song",
        output_path=str(tmp_path)
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mock_create_story = mocker.patch('artistrack.artistrack.create_story')
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    mocker.patch('artistrack.artistrack.recreate_db')
    mocker.patch('artistrack.artistrack.generate_discography')
    
    # Run main
    main()
    
    # Verify story generation was called
    mock_create_story.assert_called_once_with("Test Song", str(tmp_path))

def test_main_build_discography(mocker, mock_spotify_client, mock_data_manager):
    """Test main function with --build-discography"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=False,
        verbose=False,
        newdb=False,
        build_discography=True,
        generate_story=None,
        output_path=None
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mock_generate_discography = mocker.patch('artistrack.artistrack.generate_discography')
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    mocker.patch('artistrack.artistrack.recreate_db')
    mocker.patch('artistrack.artistrack.create_story')
    
    # Run main
    main()
    
    # Verify discography generation was called
    mock_generate_discography.assert_called_once()

def test_main_newdb(mocker, mock_spotify_client, mock_data_manager):
    """Test main function with --newdb"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=False,
        verbose=False,
        newdb=True,
        build_discography=False,
        generate_story=None,
        output_path=None
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mock_recreate_db = mocker.patch('artistrack.artistrack.recreate_db')
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    mocker.patch('artistrack.artistrack.generate_discography')
    mocker.patch('artistrack.artistrack.create_story')
    
    # Run main
    main()
    
    # Verify database recreation was called
    mock_recreate_db.assert_called_once()

def test_main_all_options(mocker, mock_spotify_client, mock_data_manager, tmp_path):
    """Test main function with all options enabled"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=True,
        verbose=True,
        newdb=True,
        build_discography=True,
        generate_story="Test Song",
        output_path=str(tmp_path)
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mock_recreate_db = mocker.patch('artistrack.artistrack.recreate_db')
    mock_generate_discography = mocker.patch('artistrack.artistrack.generate_discography')
    mock_create_story = mocker.patch('artistrack.artistrack.create_story')
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    
    # Run main
    main()
    
    # Verify all functions were called
    mock_recreate_db.assert_called_once()
    mock_spotify_client.get_artist_data.assert_called_once()
    mock_spotify_client.get_all_artist_albums.assert_called_once()
    mock_generate_discography.assert_called_once()
    mock_create_story.assert_called_once_with("Test Song", str(tmp_path))

def test_main_no_options(mocker, mock_spotify_client, mock_data_manager):
    """Test main function with no options"""
    # Mock command line arguments
    args = argparse.Namespace(
        refresh_data=False,
        verbose=False,
        newdb=False,
        build_discography=False,
        generate_story=None,
        output_path=None
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=args)
    
    # Mock dependencies
    mocker.patch('artistrack.artistrack.SpotifyClient', return_value=mock_spotify_client)
    mocker.patch('artistrack.artistrack.DataManager', return_value=mock_data_manager)
    mocker.patch('artistrack.artistrack.recreate_db')
    mocker.patch('artistrack.artistrack.generate_discography')
    mocker.patch('artistrack.artistrack.create_story')
    
    # Run main
    main()
    
    # Verify no functions were called
    mock_spotify_client.get_artist_data.assert_not_called()
    mock_spotify_client.get_all_artist_albums.assert_not_called()

# pragma: no cover
