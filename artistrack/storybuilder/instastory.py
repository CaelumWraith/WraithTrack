import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap
import yaml

def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_db_path():
    """Get the path to the database file"""
    return Path(__file__).parent.parent / 'data' / 'artistrack.db'

def create_story(song_title, output_dir=None):
    """Create an Instagram story for a given song title"""
    
    # Load configuration
    config = load_config()
    
    # Connect to database
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
        return
    
    name, release_date, duration, spotify_url, spotify_uri, image_uri, album_name = song
    
    # Create a new image using config dimensions and color
    width = config['image']['width']
    height = config['image']['height']
    bg_color = config['image']['background_color']
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
    overlay = Image.new('RGBA', art.size, (*overlay_config['color'], overlay_config['opacity']))
    art.paste(overlay, (0, 0), overlay)
    
    # Paste the art onto the story
    story.paste(art, (x, y))
    
    # Download and paste Spotify QR code
    track_id = spotify_uri.split(':')[-1]
    qr_config = config['qr_code']['spotify']
    
    # Handle QR code color inversion if specified
    fg_color = qr_config['background' if qr_config['invert_colors'] else 'foreground']
    bg_color = qr_config['foreground' if qr_config['invert_colors'] else 'background']
    
    qr_url = f"{qr_config['base_url']}/{fg_color}/{bg_color}/{qr_config['size']}/{spotify_uri}"
    qr_response = requests.get(qr_url)
    qr = Image.open(BytesIO(qr_response.content))
    
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
        return
    
    # Add song title with configurable spacing
    title_y = y + config['text']['title']['vertical_offset']
    
    # Add title shadow if enabled
    if config['text']['title']['shadow']['enabled']:
        shadow_offset = config['text']['title']['shadow']['offset']
        shadow_color = config['text']['title']['shadow']['color']
        draw.text((width//2 + shadow_offset, title_y + shadow_offset), name, 
                 font=title_font, fill=shadow_color, anchor='mm')
    
    # Draw title
    draw.text((width//2, title_y), name, 
              font=title_font, fill=config['text']['title']['color'], anchor='mm')
    
    # Add album name and release date
    info_text = f"{album_name} • {release_date}"
    draw.text((width//2, title_y + title_font.size), info_text, 
              font=info_font, fill=config['text']['info']['color'], anchor='mm')
    
    # Add streaming text
    streaming_y = y + art_height + config['text']['streaming']['vertical_offset']
    draw.text((width//2, streaming_y), config['text']['streaming']['text'],
              font=info_font, fill=config['text']['info']['color'], anchor='mm')
    
    # Add Spotify link
    spotify_text = "Listen on Spotify"
    draw.text((width//2, qr_y + qr.height + 20), spotify_text,
              font=link_font, fill=config['text']['link']['color'], anchor='mm')
    
    # Save the story
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path.cwd()
    
    output_file = output_path / f"story_{name.replace(' ', '_')}.png"
    story.save(output_file)
    print(f"Story saved to {output_file}")
    
    return output_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        song_title = " ".join(sys.argv[1:])
        create_story(song_title)
