import streamlit as st
import yaml
import os
from pathlib import Path
import pandas as pd
from artistrack.data.data_manager import DataManager
from artistrack.discotech.spotify_client import SpotifyClient
from artistrack.storybuilder.instastory import create_story
from artistrack.discotech.generate_discography import format_date
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def load_story_config():
    """Load story configuration"""
    config_path = Path(__file__).parent / 'storybuilder' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_story_config(config):
    """Save story configuration"""
    config_path = Path(__file__).parent / 'storybuilder' / 'config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)

def setup_page():
    """Configure the Streamlit page"""
    st.set_page_config(
        page_title="ArtisTrack",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("ArtisTrack")

def format_duration(duration):
    """Format duration to MM:SS"""
    if isinstance(duration, str):
        if ':' in duration:  # Already in M:SS format
            return duration
        try:
            duration = int(duration)
        except ValueError:
            return "0:00"
    
    minutes = int(duration / 60000)
    seconds = int((duration / 1000) % 60)
    return f"{minutes}:{seconds:02d}"

def get_discography_data(conn):
    """Get discography data from database"""
    # Get all albums with their tracks
    albums_df = pd.read_sql_query("""
        SELECT 
            a.album_id,
            a.name as album_name,
            a.release_date,
            a.spotify_url,
            a.album_type,
            COUNT(s.song_id) as track_count,
            a.image_thumb_uri,
            a.image_medium_uri,
            a.image_large_uri,
            a.qr_code_url
        FROM albums a
        LEFT JOIN songs s ON a.album_id = s.album_id
        GROUP BY a.album_id
        ORDER BY a.release_date DESC
    """, conn)
    
    # Get all singles
    singles_df = pd.read_sql_query("""
        SELECT 
            s.song_id,
            s.name as track_name,
            s.release_date,
            s.spotify_url,
            s.duration,
            s.qr_code_url,
            s.image_large_uri,
            s.image_medium_uri,
            s.image_thumb_uri
        FROM songs s
        WHERE s.album_id IS NULL
        ORDER BY s.release_date DESC
    """, conn)
    
    # Format the albums dataframe
    albums_df['release_date'] = albums_df['release_date'].apply(format_date)
    albums_df['spotify_link'] = albums_df['spotify_url'].apply(lambda x: f"[Open in Spotify]({x})")
    albums_df['thumbnail'] = albums_df['image_thumb_uri'].apply(lambda x: f"[![]({x})]({x})")
    albums_df['qr_code'] = albums_df['qr_code_url'].apply(lambda x: f"[![QR]({x})]({x})")
    albums_df = albums_df[[
        'thumbnail', 'album_name', 'release_date', 'album_type', 
        'track_count', 'spotify_link', 'qr_code'
    ]]
    albums_df.columns = ['Cover', 'Name', 'Release Date', 'Type', 'Tracks', 'Spotify', 'QR Code']
    
    # Format the singles dataframe
    singles_df['release_date'] = singles_df['release_date'].apply(format_date)
    singles_df['spotify_link'] = singles_df['spotify_url'].apply(lambda x: f"[Open in Spotify]({x})")
    singles_df['duration'] = singles_df['duration'].apply(format_duration)
    singles_df['thumbnail'] = singles_df['image_thumb_uri'].apply(lambda x: f"[![]({x})]({x})")
    singles_df['qr_code'] = singles_df['qr_code_url'].apply(lambda x: f"[![QR]({x})]({x})")
    singles_df = singles_df[[
        'thumbnail', 'track_name', 'release_date', 'duration', 
        'spotify_link', 'qr_code'
    ]]
    singles_df.columns = ['Cover', 'Name', 'Release Date', 'Duration', 'Spotify', 'QR Code']
    
    return albums_df, singles_df

def discography_tab():
    """Discography management tab"""
    st.header("Discography")
    
    # Initialize DataManager
    data_manager = DataManager()
    conn = data_manager.get_connection()
    cursor = conn.cursor()
    
    # Get database stats
    cursor.execute("SELECT COUNT(*) FROM albums")
    album_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM songs")
    song_count = cursor.fetchone()[0]
    
    # Display stats in a neat format
    col1, col2 = st.columns(2)
    col1.metric("Total Albums", album_count)
    col2.metric("Total Songs", song_count)
    
    # Get all tracks (both album tracks and singles) in one query
    cursor.execute("""
        WITH album_track_counts AS (
            SELECT 
                a.album_id,
                COUNT(s.song_id) as track_count,
                MAX(CASE WHEN a.name = s.name THEN 1 ELSE 0 END) as name_matches
            FROM albums a
            LEFT JOIN songs s ON a.album_id = s.album_id
            WHERE LOWER(a.name) NOT LIKE '%test%'
            GROUP BY a.album_id
        )
        
        -- Album tracks
        SELECT 
            s.name as track_name,
            CASE 
                WHEN atc.track_count = 1 AND atc.name_matches = 1 THEN 'Single'
                ELSE a.name 
            END as album_name,
            a.release_date,
            s.track_number,
            s.duration,
            s.spotify_url as track_url,
            s.qr_code_url as track_qr,
            COALESCE(a.image_large_uri, s.image_large_uri) as image_large,
            COALESCE(a.image_medium_uri, s.image_medium_uri) as image_medium,
            COALESCE(a.image_thumb_uri, s.image_thumb_uri) as image_thumb
        FROM albums a
        JOIN songs s ON a.album_id = s.album_id
        JOIN album_track_counts atc ON a.album_id = atc.album_id
        WHERE LOWER(s.name) NOT LIKE '%test%'
        
        UNION ALL
        
        -- Singles (no album)
        SELECT 
            s.name as track_name,
            'Single' as album_name,
            s.release_date,
            NULL as track_number,
            s.duration,
            s.spotify_url as track_url,
            s.qr_code_url as track_qr,
            s.image_large_uri as image_large,
            s.image_medium_uri as image_medium,
            s.image_thumb_uri as image_thumb
        FROM songs s
        WHERE s.album_id IS NULL
        AND LOWER(s.name) NOT LIKE '%test%'
        
        ORDER BY release_date DESC, album_name, track_number
    """)
    
    tracks = cursor.fetchall()
    
    # Custom CSS for the discography
    st.markdown("""
        <style>
        .stDiscography img {
            border-radius: 4px;
            transition: transform 0.3s ease;
        }
        .stDiscography img:hover {
            transform: scale(1.1);
        }
        .stDiscography .duration {
            color: #666;
            font-size: 0.9em;
        }
        .stDiscography .header {
            font-weight: bold;
            border-bottom: 2px solid #ddd;
            margin-bottom: 10px;
        }
        .stDiscography .row {
            border-bottom: 1px solid #f0f0f0;
            padding: 4px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display header
    st.markdown("""
    <div class="stDiscography">
        <table width="100%" class="header">
            <tr>
                <td width="64"></td>
                <td width="150">Album</td>
                <td width="50">#</td>
                <td width="200">Track</td>
                <td width="150">Release Date</td>
                <td width="80">Duration</td>
                <td>Links</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Display all tracks
    for track in tracks:
        track_name, album_name, release_date, track_num, duration, track_url, track_qr, large_img, medium_img, thumb_img = track
        
        st.markdown(f"""
        <div class="stDiscography">
            <table width="100%" class="row">
                <tr>
                    <td width="64">
                        <a href="{large_img}" target="_blank">
                            <img src="{thumb_img}" width="64" height="64" alt="{track_name}">
                        </a>
                    </td>
                    <td width="150">{album_name}</td>
                    <td width="50">{track_num if track_num else ''}</td>
                    <td width="200">
                        <a href="{track_url}" target="_blank">{track_name}</a>
                    </td>
                    <td width="150">{format_date(release_date)}</td>
                    <td width="80" class="duration">{duration if duration else ''}</td>
                    <td>
                        <a href="{large_img}" target="_blank">640x640</a> |
                        <a href="{medium_img}" target="_blank">300x300</a> |
                        <a href="{thumb_img}" target="_blank">64x64</a> |
                        <a href="{track_qr}" target="_blank">QR Code</a>
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    # Clean up
    conn.close()

def get_play_data(cursor, song_id, period):
    """Get play data for a song over a time period"""
    end_date = datetime.now().date()
    
    if period == "Last 7 Days":
        start_date = end_date - timedelta(days=7)
        group_by = 'play_date'
        date_format = '%Y-%m-%d'
        freq = 'D'
    elif period == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
        group_by = 'play_date'
        date_format = '%Y-%m-%d'
        freq = 'D'
    elif period == "Last 12 Months":
        start_date = end_date - timedelta(days=365)
        group_by = "strftime('%Y-%m', play_date)"
        date_format = '%Y-%m'
        freq = 'M'
    else:  # All Time
        start_date = datetime(2000, 1, 1).date()  # Far past date
        group_by = "strftime('%Y-%m', play_date)"
        date_format = '%Y-%m'
        freq = 'M'
    
    # Get play counts grouped by date
    cursor.execute(f"""
        SELECT 
            {group_by} as date,
            SUM(play_count) as plays
        FROM plays
        WHERE song_id = ? 
        AND play_date BETWEEN ? AND ?
        GROUP BY {group_by}
        ORDER BY date
    """, (song_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    
    plays = cursor.fetchall()
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(plays, columns=['date', 'plays'])
    
    # Generate complete date range
    if freq == 'D':
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        date_range = date_range.strftime(date_format)
    else:
        # For monthly data, use period_range to get YYYY-MM format
        date_range = pd.period_range(start=start_date, end=end_date, freq=freq).astype(str)
    
    # Create complete DataFrame with all dates
    full_df = pd.DataFrame({'date': date_range})
    
    if not df.empty:
        # Merge with actual play data
        full_df = full_df.merge(df, on='date', how='left')
    else:
        # No plays, add plays column with zeros
        full_df['plays'] = 0
    
    # Fill NaN values with 0
    full_df['plays'] = full_df['plays'].fillna(0)
    
    return full_df

def stats_tab():
    """Stats tab for viewing song details"""
    st.header("Song Stats")
    
    # Initialize DataManager and SpotifyClient
    data_manager = DataManager()
    spotify_client = SpotifyClient()
    conn = data_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all songs for dropdown
        cursor.execute("""
            SELECT DISTINCT 
                s.name,
                s.song_id,
                s.spotify_uri,
                COALESCE(a.name, 'Single') as album_name
            FROM songs s
            LEFT JOIN albums a ON s.album_id = a.album_id
            ORDER BY s.name
        """)
        songs = cursor.fetchall()
        
        # Create song options with album info
        song_options = [f"{song[0]} ({song[3]})" for song in songs]
        song_data = [(song[1], song[2]) for song in songs]  # (song_id, spotify_uri)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Song selection dropdown
            selected_idx = st.selectbox(
                "Select Song",
                range(len(song_options)),
                format_func=lambda x: song_options[x]
            )
        
        if selected_idx is not None:
            selected_song_id, spotify_uri = song_data[selected_idx]
            
            # Get track popularity and details from Spotify
            track_details = spotify_client.get_track_popularity(spotify_uri)
            
            if track_details:
                # Create popularity gauge chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = track_details['popularity'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Popularity Score"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 33], 'color': "lightgray"},
                            {'range': [33, 66], 'color': "gray"},
                            {'range': [66, 100], 'color': "darkgray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': track_details['popularity']
                        }
                    }
                ))
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=50, b=10),
                )
                
                # Display popularity gauge
                st.plotly_chart(fig, use_container_width=True)
                
                # Display track metrics
                col3, col4, col5 = st.columns(3)
                
                # Format metrics
                markets = track_details['available_markets']
                duration = track_details['duration_ms'] / 1000  # Convert to seconds
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                
                col3.metric("Available Markets", f"{markets:,}")
                col4.metric("Duration", f"{minutes}:{seconds:02d}")
                col5.metric("Explicit", "Yes" if track_details['explicit'] else "No")
                
                # Get artist's top tracks for comparison
                top_tracks = spotify_client.get_artist_top_tracks()
                
                if top_tracks:
                    st.write("---")
                    st.subheader("Artist's Top Tracks")
                    
                    # Create DataFrame for top tracks
                    top_df = pd.DataFrame(top_tracks)
                    
                    # Create bar chart of top track popularities
                    fig = go.Figure()
                    
                    # Add bars
                    fig.add_trace(go.Bar(
                        x=top_df['name'],
                        y=top_df['popularity'],
                        marker_color=['royalblue' if id != spotify_uri.split(':')[-1] else 'red' 
                                    for id in top_df['id']],
                        hovertemplate='%{x}<br>Popularity: %{y}<extra></extra>'
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Top Tracks Popularity Comparison",
                        xaxis_title="Track",
                        yaxis_title="Popularity Score",
                        showlegend=False,
                        xaxis={'tickangle': 45},
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=100)
                    )
                    
                    # Display chart
                    st.plotly_chart(fig, use_container_width=True)
            
            # Get detailed song info
            cursor.execute("""
                SELECT 
                    s.name,
                    s.release_date,
                    s.duration,
                    s.spotify_url,
                    s.spotify_uri,
                    s.image_large_uri,
                    s.track_number,
                    a.name as album_name,
                    a.album_type,
                    a.release_date as album_release_date,
                    (
                        SELECT COUNT(*) 
                        FROM songs s2 
                        WHERE s2.album_id = a.album_id
                    ) as album_track_count
                FROM songs s
                LEFT JOIN albums a ON s.album_id = a.album_id
                WHERE s.song_id = ?
            """, (selected_song_id,))
            
            song = cursor.fetchone()
            
            if song:
                st.write("---")
                
                # Display song artwork and basic info
                col6, col7 = st.columns([1, 2])
                
                with col6:
                    st.image(song[5], width=300)  # image_large_uri
                
                with col7:
                    st.subheader(song[0])  # name
                    if song[7]:  # album_name
                        st.write(f"**Album:** {song[7]}")
                        st.write(f"**Album Type:** {song[8]}")  # album_type
                        st.write(f"**Track Number:** {song[6]}")  # track_number
                        st.write(f"**Total Tracks:** {song[10]}")  # album_track_count
                    else:
                        st.write("**Type:** Single")
                    
                    st.write(f"**Release Date:** {format_date(song[1])}")  # release_date
                    st.write(f"**Duration:** {format_duration(song[2])}")  # duration
                    
                    # Links section
                    st.write("---")
                    st.write("**Links:**")
                    col8, col9 = st.columns(2)
                    
                    with col8:
                        st.markdown(f"[Open in Spotify]({song[3]})")  # spotify_url
                    
                    with col9:
                        qr_url = f"https://scannables.scdn.co/uri/plain/png/ffffff/black/300/{song[4]}"  # spotify_uri
                        st.markdown(f"[View QR Code]({qr_url})")
                
                # Display artwork links
                st.write("---")
                st.write("**Artwork:**")
                st.markdown(f"""
                    - [Large (640x640)]({song[5]})
                    - [Medium (300x300)]({song[5].replace('640x640', '300x300')})
                    - [Small (64x64)]({song[5].replace('640x640', '64x64')})
                """)
                
                # If part of an album, show album release info
                if song[7] and song[9]:  # album_name and album_release_date
                    st.write("---")
                    st.write("**Album Information:**")
                    st.write(f"Album Release Date: {format_date(song[9])}")
                    
                    # Calculate days between song and album release
                    try:
                        song_date = datetime.strptime(song[1], '%Y-%m-%d')
                        album_date = datetime.strptime(song[9], '%Y-%m-%d')
                        days_diff = abs((song_date - album_date).days)
                        
                        if days_diff > 0:
                            if song_date < album_date:
                                st.write(f"Released {days_diff} days before album")
                            else:
                                st.write(f"Released {days_diff} days after album")
                    except ValueError:
                        pass  # Skip if dates are not in correct format
    
    finally:
        conn.close()

def storybuilder_tab():
    """Story builder tab"""
    st.header("Story Builder")
    
    # Load current configuration
    config = load_story_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Story")
        
        # Song selection
        data_manager = DataManager()
        conn = data_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT name FROM songs ORDER BY name")
        songs = [row[0] for row in cursor.fetchall()]
        
        selected_song = st.selectbox("Select Song", songs)
        
        # Story preview container
        preview_container = st.empty()
        
        # Generated story path
        if "story_path" not in st.session_state:
            st.session_state.story_path = None
        
        if st.button("Generate Story", key="gen_story"):
            with st.spinner("Generating story..."):
                output_path = create_story(selected_song)
                if output_path:
                    st.session_state.story_path = output_path
                    # Show preview
                    with preview_container:
                        st.image(str(output_path), caption="Story Preview")
                    st.success("Story generated successfully!")
                else:
                    st.error("Failed to generate story")
        
        # Save functionality
        if st.session_state.story_path:
            st.write("---")
            st.subheader("Save Story")
            save_path = st.text_input(
                "Save Location", 
                value=str(Path.home() / "Downloads" / f"story_{selected_song.replace(' ', '_')}.png"),
                help="Enter the full path where you want to save the story"
            )
            
            if st.button("Save Story", key="save_story"):
                try:
                    # Ensure directory exists
                    save_dir = Path(save_path).parent
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to new location
                    import shutil
                    shutil.copy2(st.session_state.story_path, save_path)
                    st.success(f"Story saved to: {save_path}")
                except Exception as e:
                    st.error(f"Error saving story: {str(e)}")
        
        # Clean up
        conn.close()
    
    with col2:
        st.subheader("Configuration")
        
        # Image settings
        st.write("Image Settings")
        config['image']['width'] = st.number_input("Width", value=config['image']['width'])
        config['image']['height'] = st.number_input("Height", value=config['image']['height'])
        config['image']['background_color'] = st.color_picker("Background Color", config['image']['background_color'])
        
        # QR Code settings
        st.write("QR Code Settings")
        config['qr_code']['spotify']['invert_colors'] = st.checkbox(
            "Invert QR Colors", 
            value=config['qr_code']['spotify']['invert_colors']
        )
        
        # Text settings
        st.write("---")
        st.write("Text Settings")
        
        # Title text settings
        st.write("Title Text")
        title_col1, title_col2 = st.columns(2)
        with title_col1:
            config['text']['title']['font']['size'] = st.number_input(
                "Title Size",
                min_value=10,
                max_value=200,
                value=config['text']['title']['font']['size']
            )
        with title_col2:
            config['text']['title']['alignment'] = st.selectbox(
                "Title Alignment",
                options=["left", "center", "right"],
                index=["left", "center", "right"].index(config['text']['title']['alignment'])
            )
        
        # Info text settings
        st.write("Info Text")
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            config['text']['info']['font']['size'] = st.number_input(
                "Info Size",
                min_value=10,
                max_value=100,
                value=config['text']['info']['font']['size']
            )
        with info_col2:
            config['text']['info']['alignment'] = st.selectbox(
                "Info Alignment",
                options=["left", "center", "right"],
                index=["left", "center", "right"].index(config['text']['info']['alignment'])
            )
        
        # Link text settings
        st.write("Link Text")
        link_col1, link_col2 = st.columns(2)
        with link_col1:
            config['text']['link']['font']['size'] = st.number_input(
                "Link Size",
                min_value=10,
                max_value=100,
                value=config['text']['link']['font']['size']
            )
        with link_col2:
            config['text']['link']['alignment'] = st.selectbox(
                "Link Alignment",
                options=["left", "center", "right"],
                index=["left", "center", "right"].index(config['text']['link']['alignment'])
            )
        
        # Streaming text settings
        st.write("Streaming Text")
        stream_col1, stream_col2 = st.columns(2)
        with stream_col1:
            config['text']['streaming']['text'] = st.text_area(
                "Text Content",
                value=config['text']['streaming']['text']
            )
        with stream_col2:
            config['text']['streaming']['alignment'] = st.selectbox(
                "Streaming Text Alignment",
                options=["left", "center", "right"],
                index=["left", "center", "right"].index(config['text']['streaming']['alignment'])
            )
        
        if st.button("Save Configuration", key="save_config"):
            save_story_config(config)
            st.success("Configuration saved!")
            # Clear the current preview and story path when config changes
            preview_container.empty()
            st.session_state.story_path = None

def setup_tab():
    """Setup tab"""
    st.header("Setup")
    
    # Spotify credentials
    st.subheader("Spotify API Credentials")
    
    current_client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    current_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    new_client_id = st.text_input("Client ID", value=current_client_id, type="password")
    new_client_secret = st.text_input("Client Secret", value=current_client_secret, type="password")
    
    if st.button("Save Credentials", key="save_creds"):
        # Update .env file
        env_path = Path(__file__).parent.parent / '.env'
        
        env_content = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.readlines()
        
        # Update or add credentials
        updated_id = False
        updated_secret = False
        
        for i, line in enumerate(env_content):
            if line.startswith('SPOTIFY_CLIENT_ID='):
                env_content[i] = f'SPOTIFY_CLIENT_ID={new_client_id}\n'
                updated_id = True
            elif line.startswith('SPOTIFY_CLIENT_SECRET='):
                env_content[i] = f'SPOTIFY_CLIENT_SECRET={new_client_secret}\n'
                updated_secret = True
        
        if not updated_id:
            env_content.append(f'SPOTIFY_CLIENT_ID={new_client_id}\n')
        if not updated_secret:
            env_content.append(f'SPOTIFY_CLIENT_SECRET={new_client_secret}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(env_content)
        
        st.success("Credentials saved! Please restart the application for changes to take effect.")
    
    # Database management
    st.write("---")
    st.subheader("Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Initialize Database", key="init_db"):
            from artistrack.data.model import init_db
            init_db()
            st.success("Database initialized!")
        
        if st.button("Reset Database", key="reset_db"):
            if st.checkbox("I understand this will delete all data"):
                from artistrack.data.model import recreate_db
                recreate_db()
                st.success("Database reset successfully!")
    
    with col2:
        if st.button("Refresh Artist Data", key="refresh_data"):
            with st.spinner("Fetching artist data..."):
                spotify = SpotifyClient()
                data_manager = DataManager()
                
                # Get artist data
                st.write("Fetching artist data...")
                artist_data = spotify.get_artist_data()
                
                # Get all albums
                st.write("Fetching artist albums...")
                albums = spotify.get_all_artist_albums()
                
                # Process each album
                progress_bar = st.progress(0)
                for i, album_data in enumerate(albums, 1):
                    # Save album
                    album = data_manager.save_album(album_data)
                    st.write(f"Saved album: {album.name}")
                    
                    # Get and save all tracks for this album
                    tracks = spotify.get_album_tracks(album_data['id'])
                    for track_data in tracks:
                        track_data['images'] = album_data['images']
                        track_data['release_date'] = album_data['release_date']
                        data_manager.save_song(track_data, album.album_id)
                    
                    progress_bar.progress(i / len(albums))
                
                st.success("Database updated successfully!")

def main():
    """Main application entry point"""
    setup_page()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Discography", "Story Builder", "Stats", "Setup"])
    
    with tab1:
        discography_tab()
    
    with tab2:
        storybuilder_tab()
    
    with tab3:
        stats_tab()
    
    with tab4:
        setup_tab()

if __name__ == "__main__":
    main()
