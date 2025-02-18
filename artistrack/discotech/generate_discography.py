import sqlite3
from pathlib import Path
from datetime import datetime

def get_db_path():
    """Get the path to the database file"""
    return Path(__file__).parent.parent / 'data' / 'artistrack.db'

def format_date(date_str):
    """Convert YYYY-MM-DD to Month DD, YYYY format"""
    if not date_str or not isinstance(date_str, str):
        return "Unknown Date"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except ValueError:
        # Try partial date formats
        try:
            if len(date_str) == 4:  # Just year
                return date_str
            elif len(date_str) == 7:  # Year and month
                date_obj = datetime.strptime(date_str, '%Y-%m')
                return date_obj.strftime('%B %Y')
            else:
                return "Invalid Date Format"
        except ValueError:
            return "Invalid Date Format"

def generate_discography(output_dir=None):
    """Generate discography HTML from the database.
    
    Args:
        output_dir: Optional directory to save the file. If None, uses current directory.
    
    Returns:
        Path object pointing to the generated HTML file.
    """
    # Get database path
    db_path = get_db_path()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all albums with their tracks
    cursor.execute("""
        SELECT 
            a.album_id,
            a.name as album_name,
            a.release_date,
            a.spotify_url,
            a.album_type,
            a.qr_code_url,
            a.image_large_uri,
            a.image_medium_uri,
            a.image_thumb_uri,
            s.name as track_name,
            s.track_number,
            s.spotify_url as track_url,
            s.qr_code_url as track_qr_url,
            s.duration
        FROM albums a
        LEFT JOIN songs s ON a.album_id = s.album_id
        ORDER BY a.release_date DESC, s.track_number ASC
    """)
    
    albums = cursor.fetchall()
    
    # Get all singles (songs without album_id)
    cursor.execute("""
        SELECT 
            song_id,
            name,
            release_date,
            spotify_url,
            qr_code_url,
            duration,
            image_large_uri,
            image_medium_uri,
            image_thumb_uri
        FROM songs
        WHERE album_id IS NULL
        ORDER BY release_date DESC
    """)
    
    singles = cursor.fetchall()
    
    # Generate HTML
    html = """<!DOCTYPE html>
    <html>
    <head>
        <title>Caelum Wraith Discography</title>
        <style>
            .discography {
                border-collapse: collapse;
                width: 100%;
                max-width: 1200px;
                margin: 20px auto;
            }
            .discography th, .discography td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .discography img {
                display: block;
                transition: transform 0.3s ease;
            }
            .thumbnail:hover img {
                transform: scale(1.1);
            }
            .discography a {
                color: #000;
                text-decoration: none;
            }
            .discography a:hover {
                text-decoration: underline;
            }
            .image-links a {
                color: #666;
                font-size: 0.9em;
                margin: 0 5px;
            }
            .image-links a:hover {
                color: #000;
            }
            .track-row {
                background-color: #f9f9f9;
            }
            .track-row td {
                padding-left: 30px;
            }
            .duration {
                color: #666;
                font-size: 0.9em;
            }
            .qr-link {
                color: #666;
                font-size: 0.9em;
                margin-left: 10px;
            }
            .qr-link:hover {
                color: #000;
            }
            .empty-message {
                text-align: center;
                padding: 40px;
                color: #666;
                font-size: 1.2em;
            }
        </style>
    </head>
    <body>
        <table class="discography">
            <thead>
                <tr>
                    <th></th>
                    <th>Type</th>
                    <th>Track</th>
                    <th>Release Date</th>
                    <th>Duration</th>
                    <th>Links</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if not albums and not singles:
        html += """
                <tr>
                    <td colspan="6" class="empty-message">No albums found in database</td>
                </tr>
"""
    else:
        # Process albums
        current_album_id = None
        for row in albums:
            album_id, album_name, release_date, spotify_url, album_type, qr_url, large_img, medium_img, thumb_img, track_name, track_num, track_url, track_qr_url, duration = row
            
            if album_id != current_album_id:
                # New album header
                html += f"""
        <tr class="main-row">
            <td>
                <a href="{large_img}" target="_blank" class="thumbnail">
                    <img src="{thumb_img}" width="64" height="64" alt="{album_name}">
                </a>
            </td>
            <td>Album</td>
            <td><a href="{spotify_url}" target="_blank">{album_name}</a></td>
            <td>{format_date(release_date)}</td>
            <td></td>
            <td>
                <a href="{large_img}" target="_blank">640x640</a> |
                <a href="{medium_img}" target="_blank">300x300</a> |
                <a href="{thumb_img}" target="_blank">64x64</a>
                <a href="{qr_url}" target="_blank" class="qr-link">QR Code</a>
            </td>
        </tr>"""
                current_album_id = album_id
            
            if track_name:
                # Add track row
                html += f"""
        <tr class="track-row">
            <td></td>
            <td></td>
            <td><a href="{track_url}" target="_blank">{track_name}</a></td>
            <td></td>
            <td class="duration">{duration}</td>
            <td><a href="{track_qr_url}" target="_blank" class="qr-link">QR Code</a></td>
        </tr>"""
        
        # Process singles
        for row in singles:
            song_id, name, release_date, spotify_url, qr_url, duration, large_img, medium_img, thumb_img = row
            html += f"""
        <tr class="main-row">
            <td>
                <a href="{large_img}" target="_blank" class="thumbnail">
                    <img src="{thumb_img}" width="64" height="64" alt="{name}">
                </a>
            </td>
            <td>Single</td>
            <td><a href="{spotify_url}" target="_blank">{name}</a></td>
            <td>{format_date(release_date)}</td>
            <td class="duration">{duration}</td>
            <td>
                <a href="{large_img}" target="_blank">640x640</a> |
                <a href="{medium_img}" target="_blank">300x300</a> |
                <a href="{thumb_img}" target="_blank">64x64</a>
                <a href="{qr_url}" target="_blank" class="qr-link">QR Code</a>
            </td>
        </tr>"""
    
    # Close HTML
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Close database connection
    conn.close()
    
    # Determine output path
    if output_dir is None:
        output_dir = Path.cwd()
    elif isinstance(output_dir, str):
        output_dir = Path(output_dir)
    
    output_path = output_dir / 'discography.html'
    
    # Write HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Generated discography at {output_path}")
    return output_path

if __name__ == "__main__":
    generate_discography()