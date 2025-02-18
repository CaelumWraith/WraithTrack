# ArtisTrack

ArtisTrack is a Python-based tool for tracking and managing artist discographies on Spotify, with features for generating Instagram stories to showcase music updates.

## Features

- **Spotify Integration**: Seamlessly fetch and manage artist data from Spotify
- **Discography Management**: Local SQLite database for storing and tracking artist releases
- **Story Generation**: Create beautiful Instagram stories for music updates
- **Customizable Design**: Configurable story layouts, fonts, colors, and QR codes
- **Automated Updates**: Track and showcase new releases automatically

## Prerequisites

- Python 3.x
- Spotify API credentials (Client ID and Client Secret)
- Instagram account (for story posting)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/artistrack.git
cd artistrack
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with your Spotify API credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

## Usage

### Running the Application

Start the application:
```bash
python run-web.py
```

### Story Generation

1. **Story Builder**:
   - Select a song from your discography
   - Customize the story design (colors, fonts, layout)
   - Preview and generate the story
   - Save to your preferred location

2. **Configuration**:
   - Adjust image dimensions and background colors
   - Customize QR code appearance
   - Configure text styles and positions
   - Set streaming text and alignment

### Story Configuration

The story generator supports extensive customization through `config.yaml`:

```yaml
image:
  width: 1080
  height: 1300
  background_color: '#000000'
  artwork:
    padding: 100
    vertical_offset: -20

text:
  title:
    font:
      name: 'Game Of Squids.ttf'
      size: 100
    alignment: 'center'
  
  streaming:
    text: 'NOW STREAMING'
    alignment: 'right'
```

## Project Structure

- `artistrack/`
  - `data/` - Database management and data models
  - `discotech/` - Spotify API integration
  - `storybuilder/` - Instagram story generation
    - `fonts/` - Custom fonts for story text
    - `config.yaml` - Story design configuration

## Testing

Run the test suite using pytest:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=artistrack
```

## Dependencies

- pillow - Image processing
- streamlit - Web interface
- pytest - Testing framework
- requests - HTTP client
- python-dotenv - Environment variable management
- pyyaml - Configuration management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.