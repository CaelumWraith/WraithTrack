import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap
import yaml
import re
from PIL import ImageColor

def parse_color(color):
    """Parse color string to RGB tuple"""
    if not color:
        return (0, 0, 0)  # Default to black
        
    # If it's already an RGB tuple
    if isinstance(color, (list, tuple)) and len(color) == 3:
        return tuple(color)
        
    try:
        # Try to parse as hex or named color using PIL
        return ImageColor.getrgb(color)
    except ValueError:
        # Default to black if invalid
        return (0, 0, 0)

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    return parse_color(hex_color)

def hex_to_name(hex_color):
    """Convert hex color to a basic name for Spotify QR codes"""
    # Remove any '#' prefix
    hex_color = hex_color.lstrip('#') if isinstance(hex_color, str) else ''
    
    # Basic color mapping for Spotify QR codes
    color_map = {
        '000000': 'black',
        'ffffff': 'white',
        'ff0000': 'red',
        '00ff00': 'green',
        '0000ff': 'blue',
    }
    
    # If it's already a named color, return it
    if isinstance(hex_color, str) and hex_color.lower() in ['black', 'white', 'red', 'green', 'blue']:
        return hex_color.lower()
    
    # Try to map hex to name
    return color_map.get(hex_color.lower(), 'black')  # Default to black if no match

def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_db_path():
    """Get the path to the database file"""
    return Path(__file__).parent.parent / 'data' / 'artistrack.db'

def get_text_anchor(alignment):
    """Convert alignment string to PIL anchor point"""
    if alignment == "left":
        return "lm"
    elif alignment == "right":
        return "rm"
    else:  # center
        return "mm"

def get_text_position(alignment, width, x):
    """Get x position based on alignment"""
    if alignment == "left":
        return x
    elif alignment == "right":
        return width - x
    else:  # center
        return width // 2

def create_story(song_title, output_dir=None):
    """Create an Instagram story for a given song title"""
    
    # Load configuration - let FileNotFoundError propagate
    config = load_config()
    
    # Validate width is an integer
    try:
        width = int(config['image']['width'])
        height = int(config['image']['height'])
    except (ValueError, TypeError) as e:
        raise TypeError("Image dimensions must be integers") from e
    
    # Connect to database
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find the song (either album track or single)
        cursor.execute("""
            SELECT 
                s.name,
                s.release_date,
                s.duration,
                s.spotify_url,
                s.spotify_uri,
                s.image_large_uri,
                COALESCE(a.name, 'Single') as album_name
            FROM songs s
            LEFT JOIN albums a ON s.album_id = a.album_id
            WHERE LOWER(s.name) = LOWER(?)
        """, (song_title,))
        
        song = cursor.fetchone()
        
        if not song:
            print(f"Song '{song_title}' not found in database")
            return None
        
        name, release_date, duration, spotify_url, spotify_uri, image_uri, album_name = song
        
        # Create a new image using config dimensions and color
        bg_color = parse_color(config['image']['background_color'])
        story = Image.new('RGB', (width, height), color=bg_color)
        
        # Download and paste the song art
        response = requests.get(image_uri)
        art = Image.open(BytesIO(response.content))
        
        # Resize art to fit width while maintaining aspect ratio
        padding = config['image']['artwork']['padding']
        art_width = width - (2 * padding)
        art_height = int(art_width * art.height / art.width)
        art = art.resize((art_width, art_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the art
        x = (width - art_width) // 2
        y = (height - art_height) // 2 + config['image']['artwork']['vertical_offset']
        
        # Create semi-transparent overlay
        overlay_config = config['image']['artwork']['overlay']
        overlay = Image.new('RGBA', art.size, (*parse_color(overlay_config['color']), overlay_config['opacity']))
        art.paste(overlay, (0, 0), overlay)
        
        # Paste the art onto the story
        story.paste(art, (x, y))
        
        # Download and paste Spotify QR code
        track_id = spotify_uri.split(':')[-1]
        qr_config = config['qr_code']['spotify']
        
        # Get QR code colors
        fg_color = qr_config['foreground'].lstrip('#')  # Remove # if present
        bg_color = qr_config['background']  # Keep as named color
        
        # Handle QR code color inversion if specified
        if qr_config['invert_colors']:
            # Convert named colors to hex
            if bg_color == 'black':
                bg_color = 'ffffff'
                fg_color = '000000'
            elif bg_color == 'white':
                bg_color = '000000'
                fg_color = 'ffffff'
            else:
                # Swap colors as-is
                fg_color, bg_color = bg_color, fg_color
        
        qr_url = f"{qr_config['base_url']}/{fg_color}/{bg_color}/{qr_config['size']}/{spotify_uri}"
        qr_response = requests.get(qr_url)
        if qr_response.status_code != 200:
            print(f"Error getting QR code: {qr_response.status_code}")
            print(f"Response content: {qr_response.content[:200]}")
            return None
        
        try:
            qr = Image.open(BytesIO(qr_response.content))
        except Exception as e:
            print(f"Error opening QR code image: {e}")
            print(f"Response content type: {qr_response.headers.get('content-type')}")
            return None
        
        # Calculate position for QR code
        qr_x = (width - qr.width) // 2
        qr_y = y + art_height + qr_config['vertical_offset']
        
        # Paste QR code
        story.paste(qr, (qr_x, qr_y))
        
        # Add text
        draw = ImageDraw.Draw(story)
        
        # Load fonts
        fonts_dir = Path(__file__).parent / 'fonts'
        try:
            title_font = ImageFont.truetype(str(fonts_dir / config['text']['title']['font']['name']), 
                                          config['text']['title']['font']['size'])
            info_font = ImageFont.truetype(str(fonts_dir / config['text']['info']['font']['name']), 
                                         config['text']['info']['font']['size'])
            link_font = ImageFont.truetype(str(fonts_dir / config['text']['link']['font']['name']), 
                                         config['text']['link']['font']['size'])
        except OSError as e:
            print(f"Font error: {e}")
            print(f"Please ensure fonts are in {fonts_dir}")
            return None
        
        # Add song title with configurable spacing
        title_y = y + config['text']['title']['vertical_offset']
        title_x = get_text_position(config['text']['title']['alignment'], width, padding)
        title_anchor = get_text_anchor(config['text']['title']['alignment'])
        
        # Add title shadow if enabled
        if config['text']['title']['shadow']['enabled']:
            shadow_offset = config['text']['title']['shadow']['offset']
            shadow_color = parse_color(config['text']['title']['shadow']['color'])
            draw.text((title_x + shadow_offset, title_y + shadow_offset), name, 
                     font=title_font, fill=shadow_color, anchor=title_anchor)
        
        # Draw title
        draw.text((title_x, title_y), name, 
                  font=title_font, fill=parse_color(config['text']['title']['color']), anchor=title_anchor)
        
        # Add album name and release date
        info_text = f"{album_name} • {release_date}"
        info_x = get_text_position(config['text']['info']['alignment'], width, padding)
        draw.text((info_x, title_y + title_font.size), info_text, 
                  font=info_font, fill=parse_color(config['text']['info']['color']), 
                  anchor=get_text_anchor(config['text']['info']['alignment']))
        
        # Add streaming text
        streaming_y = y + art_height + config['text']['streaming']['vertical_offset']
        streaming_x = get_text_position(config['text']['streaming']['alignment'], width, padding)
        draw.text((streaming_x, streaming_y), config['text']['streaming']['text'],
                  font=info_font, fill=parse_color(config['text']['info']['color']), 
                  anchor=get_text_anchor(config['text']['streaming']['alignment']))
        
        # Add Spotify link text
        link_x = get_text_position(config['text']['link']['alignment'], width, padding)
        draw.text((link_x, qr_y + qr.height + 20), "Listen on Spotify",
                  font=link_font, fill=parse_color(config['text']['link']['color']), 
                  anchor=get_text_anchor(config['text']['link']['alignment']))
        
        # Save the story
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path.cwd()
        
        output_file = output_path / f"story_{name.replace(' ', '_')}.png"
        story.save(output_file)
        print(f"Story saved to {output_file}")
        
        return output_file
        
    except (TypeError, ValueError) as e:
        # Re-raise type errors (like invalid dimensions)
        raise
    except Exception as e:
        print(f"Error creating story: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        song_title = " ".join(sys.argv[1:])
        create_story(song_title)
