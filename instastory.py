import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

def create_story(song_title):
    """Create an Instagram story for a given song title"""
    
    # Connect to database
    db_path = Path('data') / 'wraith.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find the song (either album track or single)
    cursor.execute("""
        SELECT 
            s.name,
            s.release_date,
            s.duration,
            s.spotify_url,
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
    
    name, release_date, duration, spotify_url, image_uri, album_name = song
    
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
    
    # Add text
    draw = ImageDraw.Draw(story)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype('stories/fonts/Game Of Squids.ttf', 120)
        info_font = ImageFont.truetype('stories/fonts/federalescort.ttf', 45)
        link_font = ImageFont.truetype('stories/fonts/federalescort.ttf', 30)
    except OSError as e:
        print(f"Font error: {e}")
        print("Please ensure fonts are in the stories/fonts directory")
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
    
    # Add link closer to streaming text
    link_y = streaming_y + 40
    draw.text((width//2, link_y), "https://link.tr/caelumwraith", 
              font=link_font, fill='white', anchor='mm')
    
    # Save the story
    output_dir = Path('stories')
    output_dir.mkdir(exist_ok=True)
    
    safe_title = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '-')
    
    output_path = output_dir / f"story_{safe_title}.png"
    story.save(output_path)
    
    print(f"Created story at {output_path}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        song_title = " ".join(sys.argv[1:])
        create_story(song_title)
    else:
        print("Please provide a song title")
