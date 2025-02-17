import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

def get_db_path():
    """Get the path to the database file"""
    return Path(__file__).parent.parent / 'data' / 'artistrack.db'

def create_story(song_title, output_dir=None):
    """Create an Instagram story for a given song title"""
    
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
    
    # Create a new image (1080x1300)
    width = 1080
    height = 1300
    story = Image.new('RGB', (width, height), color='black')
    
    # Download and paste the song art
    response = requests.get(image_uri)
    art = Image.open(BytesIO(response.content))
    
    # Resize art to fit width while maintaining aspect ratio
    art_width = width - 200  # 100px padding on each side
    art_height = int(art_width * art.height / art.width)
    art = art.resize((art_width, art_height), Image.Resampling.LANCZOS)
    
    # Calculate position to center the art
    x = (width - art_width) // 2
    y = (height - art_height) // 2 - 20  # Reduced upward shift from 50 to 40
    
    # Create semi-transparent overlay
    overlay = Image.new('RGBA', art.size, (0, 0, 0, 128))
    art.paste(overlay, (0, 0), overlay)
    
    # Paste the art onto the story
    story.paste(art, (x, y))
    
    # Download and paste Spotify QR code
    track_id = spotify_uri.split(':')[-1]
    qr_url = f"https://scannables.scdn.co/uri/plain/png/ffffff/black/300/{spotify_uri}"
    qr_response = requests.get(qr_url)
    qr = Image.open(BytesIO(qr_response.content))
    
    # Calculate position for QR code (centered, below the streaming text)
    qr_x = (width - qr.width) // 2
    qr_y = y + art_height + 120  # Below the streaming text
    
    # Paste QR code
    story.paste(qr, (qr_x, qr_y))
    
    # Add text
    draw = ImageDraw.Draw(story)
    
    # Load fonts
    fonts_dir = Path(__file__).parent / 'fonts'
    try:
        title_font = ImageFont.truetype(str(fonts_dir / 'Game Of Squids.ttf'), 120)
        info_font = ImageFont.truetype(str(fonts_dir / 'federalescort.ttf'), 45)
        link_font = ImageFont.truetype(str(fonts_dir / 'federalescort.ttf'), 30)
    except OSError as e:
        print(f"Font error: {e}")
        print(f"Please ensure fonts are in {fonts_dir}")
        return
    
    # Add song title with more space at top
    title_y = y - 100  # Increased space above artwork
    
    # Add a slight shadow effect to the title
    shadow_offset = 3
    draw.text((width//2 + shadow_offset, title_y + shadow_offset), name, 
              font=title_font, fill='#333333', anchor='mm')
    draw.text((width//2, title_y), name, 
              font=title_font, fill='white', anchor='mm')
    
    # Add "now streaming everywhere" closer to artwork
    streaming_y = y + art_height + 40
    draw.text((width//2, streaming_y), "NOW STREAMING EVERYWHERE", 
              font=info_font, fill='white', anchor='mm')
    
    # Add "Scan to Listen" text below QR code
    scan_y = qr_y + qr.height + 20
    draw.text((width//2, scan_y), "Scan to Listen", 
              font=info_font, fill='white', anchor='mm')
    
    # Add link closer to streaming text
    link_y = streaming_y + 40
    draw.text((width//2, link_y), "https://link.tr/caelumwraith", 
              font=link_font, fill='white', anchor='mm')
    
    # Save the story
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    safe_title = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '-')
    
    output_path = output_dir / f"story_{safe_title}.png"
    story.save(output_path)
    
    print(f"Created story at {output_path}")
    
    conn.close()
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        song_title = " ".join(sys.argv[1:])
        create_story(song_title)
    else:
        print("Please provide a song title")
