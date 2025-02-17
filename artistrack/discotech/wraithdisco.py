import json
from pathlib import Path
from datetime import datetime

def get_single_html_row(single_data, row_type="single"):
    """
    Creates an HTML table row for a single track or album
    Args:
        single_data: JSON data for a single track
        row_type: Type of row ("single", "album", or "track")
    Returns:
        str: HTML table row
    """
    # Get all image sizes
    large_image = single_data['images'][0]['url']  # 640x640
    medium_image = single_data['images'][1]['url']  # 300x300
    thumbnail = single_data['images'][2]['url']     # 64x64
    
    # Get the track/album name and spotify URL
    item_name = single_data['name']
    spotify_url = single_data['external_urls']['spotify']
    
    # Format the release date
    release_date = datetime.strptime(single_data['release_date'], '%Y-%m-%d').strftime('%B %d, %Y')
    
    # Add track number for album tracks
    if row_type == "track":
        item_name = f"Track {single_data.get('track_number', '')} - {item_name}"
        row_class = "track-row"
    else:
        row_class = "main-row"
    
    # Create the HTML row with clickable thumbnail and image links
    html_row = f"""
    <tr class="{row_class}">
        <td>
            <a href="{large_image}" target="_blank" class="thumbnail">
                <img src="{thumbnail}" width="64" height="64" alt="{item_name}">
            </a>
        </td>
        <td>{row_type.title()}</td>
        <td><a href="{spotify_url}" target="_blank">{item_name}</a></td>
        <td>{release_date}</td>
        <td>
            <a href="{large_image}" target="_blank">640x640</a> |
            <a href="{medium_image}" target="_blank">300x300</a> |
            <a href="{thumbnail}" target="_blank">64x64</a>
        </td>
    </tr>
    """
    
    return html_row

def main():
    # Create disco directory if it doesn't exist
    disco_dir = Path('disco')
    disco_dir.mkdir(exist_ok=True)
    
    # Get current date for loading latest artist albums file
    data_dir = Path('data')
    current_date = datetime.now().strftime('%Y-%m-%d')
    albums_file = data_dir / f"{current_date}__artist_albums.json"
    
    # Load artist albums data
    with open(albums_file, 'r') as f:
        albums_data = json.load(f)
    
    # Sort all items by release date
    all_items = albums_data['items']
    all_items.sort(key=lambda x: x['release_date'], reverse=True)
    
    # Generate HTML table with basic styling
    html = """
    <!DOCTYPE html>
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
                    <th>Images</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Process all items
    for item in all_items:
        if item['album_type'] == 'single':
            html += get_single_html_row(item, "single")
        else:
            # Add album row
            html += get_single_html_row(item, "album")
            
            # Load album tracks data
            album_id = item['id']
            track_filename = f"{current_date}__track__{item['name']}_{album_id}.json"
            track_filepath = data_dir / track_filename
            
            if track_filepath.exists():
                with open(track_filepath, 'r') as f:
                    tracks_data = json.load(f)
                    
                # Add track rows with actual track data
                for track in tracks_data['items']:
                    track_data = item.copy()  # Copy album data for images
                    track_data['name'] = track['name']
                    track_data['track_number'] = track['track_number']
                    track_data['external_urls'] = track['external_urls']
                    html += get_single_html_row(track_data, "track")
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Save the HTML file
    output_path = disco_dir / 'discography.html'
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Discography HTML saved to {output_path}")
    print(f"Total items processed: {len(all_items)}")

if __name__ == "__main__":
    main()
