import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO
import yaml
import requests
from artistrack.storybuilder.instastory import create_story, load_config

@pytest.fixture
def mock_config(mocker):
    """Load test configuration"""
    config_path = Path(__file__).parent / 'test_config.yaml'
    with open(config_path, 'r') as f:
        test_config = yaml.safe_load(f)
    mocker.patch('artistrack.storybuilder.instastory.load_config', return_value=test_config)
    return test_config

@pytest.fixture
def mock_image_response(mocker):
    """Create a mock image response"""
    test_image = Image.new('RGB', (640, 640), 'black')
    image_bytes = BytesIO()
    test_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    mock_response = mocker.MagicMock()
    mock_response.content = image_bytes.getvalue()
    mocker.patch('requests.get', return_value=mock_response)
    return mock_response

@pytest.fixture
def mock_db(mocker):
    """Mock database connection and query"""
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
    return mock_conn

def test_load_config():
    """Test loading configuration file"""
    config = load_config()
    assert isinstance(config, dict)
    assert 'image' in config
    assert 'qr_code' in config
    assert 'text' in config

def test_create_story_with_custom_config(mock_config, mock_image_response, mock_db, tmp_path):
    """Test creating a story image with custom configuration"""
    output_path = create_story("Test Song", tmp_path)
    
    # Verify story was created
    assert output_path.exists()
    assert output_path.name == "story_Test_Song.png"
    
    # Verify image dimensions from test config
    with Image.open(output_path) as img:
        assert img.size == (
            mock_config['image']['width'],
            mock_config['image']['height']
        )
        
        # Test background color
        # Get color of pixel at corner (should be background)
        corner_color = img.getpixel((0, 0))
        assert corner_color == (255, 0, 0)  # RGB for red

def test_create_story_missing_config(mocker, mock_image_response, mock_db, tmp_path):
    """Test error handling when config file is missing"""
    mocker.patch('artistrack.storybuilder.instastory.load_config', 
                side_effect=FileNotFoundError)
    
    with pytest.raises(FileNotFoundError):
        create_story("Test Song", tmp_path)

def test_create_story_invalid_config(mocker, mock_image_response, mock_db, tmp_path):
    """Test error handling with invalid configuration"""
    invalid_config = {
        'image': {
            'width': 'invalid',
            'height': 1000,
            'background_color': 'black',
            'artwork': {
                'padding': 100,
                'vertical_offset': 0,
                'overlay': {
                    'color': [0, 0, 0],
                    'opacity': 128
                }
            }
        },
        'qr_code': {
            'spotify': {
                'base_url': 'https://scannables.scdn.co/uri/plain/png',
                'foreground': 'ffffff',
                'background': 'black',
                'size': 300,
                'vertical_offset': 120,
                'invert_colors': False
            }
        },
        'text': {
            'title': {
                'font': {'name': 'test.ttf', 'size': 120},
                'vertical_offset': -100,
                'shadow': {
                    'enabled': True,
                    'offset': 3,
                    'color': '#333333'
                },
                'color': 'white'
            },
            'info': {
                'font': {'name': 'test.ttf', 'size': 45},
                'color': 'white'
            },
            'link': {
                'font': {'name': 'test.ttf', 'size': 30},
                'color': '#cccccc'
            },
            'streaming': {
                'text': 'NOW STREAMING',
                'vertical_offset': 80
            }
        }
    }
    mocker.patch('artistrack.storybuilder.instastory.load_config', 
                return_value=invalid_config)
    
    with pytest.raises(TypeError):
        create_story("Test Song", tmp_path)

def test_create_story_song_not_found(mock_config, mock_db, tmp_path):
    """Test handling of non-existent song"""
    mock_db.cursor().fetchone.return_value = None
    
    output_path = create_story("Nonexistent Song", tmp_path)
    assert output_path is None

def test_qr_code_inversion(mock_config, mock_image_response, mock_db, tmp_path, mocker):
    """Test QR code color inversion"""
    # Spy on requests.get to capture QR code URL
    get_spy = mocker.spy(requests, 'get')
    
    create_story("Test Song", tmp_path)
    
    # Get all calls to requests.get
    calls = [call for call in get_spy.call_args_list]
    
    # Find the QR code request (second request, first is for album art)
    qr_url = calls[1][0][0]
    
    # Verify color inversion in URL
    # In test_config.yaml, invert_colors is true, so foreground/background should be swapped
    assert 'ffffff/000000' in qr_url  # Original colors were black/white

def test_text_positioning(mock_config, mock_image_response, mock_db, tmp_path):
    """Test text positioning and font configuration"""
    output_path = create_story("Test Song", tmp_path)
    
    # Verify the image was created
    assert output_path.exists()
    
    # Load the image to verify it was created with correct dimensions
    with Image.open(output_path) as img:
        # We can't easily test exact text positioning in a PIL image
        # but we can verify the image was created with the correct dimensions
        assert img.size == (
            mock_config['image']['width'],
            mock_config['image']['height']
        )
