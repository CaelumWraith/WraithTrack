import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO
from artistrack.storybuilder.instastory import create_story

def test_create_story(test_db_path, tmp_path, mocker):
    """Test creating a story image"""
    # Mock database query
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (
        "Test Song", "2025-01-01", "3:00",
        "https://open.spotify.com/track/test",
        "spotify:track:test",
        "https://example.com/large.jpg",
        "Album"
    )
    
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    mocker.patch('sqlite3.connect', return_value=mock_conn)
    
    # Create a test image and get its bytes
    test_image = Image.new('RGB', (640, 640), 'black')
    image_bytes = BytesIO()
    test_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    # Mock image download
    mock_response = mocker.MagicMock()
    mock_response.content = image_bytes.getvalue()
    mocker.patch('requests.get', return_value=mock_response)
    
    # Create story
    output_path = create_story("Test Song", tmp_path)
    
    # Verify story was created
    assert output_path.exists()
    assert output_path.name.startswith("story_")
    assert output_path.name.endswith(".png")
    
    # Verify image dimensions
    with Image.open(output_path) as img:
        assert img.size == (1080, 1300)
