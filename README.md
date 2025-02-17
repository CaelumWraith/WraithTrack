# ArtisTrack

ArtisTrack is a Python-based tool for tracking and managing artist discographies on Spotify, with features for generating Instagram stories to showcase music updates.

## Features

- Spotify artist data fetching and management
- Local SQLite database for storing artist discographies
- Automatic Instagram story generation for music updates
- Support for album and track metadata
- Beautiful visualization of music data

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

### Basic Usage

1. Initialize the database:
```bash
python -m artistrack.artistrack --init-db
```

2. Fetch artist data and populate the database:
```bash
python -m artistrack.artistrack --populate
```

3. Generate Instagram stories:
```bash
python -m artistrack.artistrack --generate-story
```

### Advanced Options

- Use `--verbose` flag for detailed logging
- Use `--recreate-db` to reset the database
- Use `--help` to see all available options

## Project Structure

- `artistrack/`
  - `data/` - Database management and data models
  - `discotech/` - Spotify API integration
  - `storybuilder/` - Instagram story generation

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
- pytest - Testing framework
- requests - HTTP client
- python-dotenv - Environment variable management
- beautifulsoup4 - HTML parsing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.