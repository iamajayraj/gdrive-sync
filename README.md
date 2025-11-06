# Google Drive Sync and Dify API Integration

This application monitors a Google Drive folder (and its subfolders) for new or modified files and pushes them to the Dify API.

## Project Structure

```
gdrive-sync/
├── config/                 # Configuration files
│   └── config.yaml.example # Example configuration file
├── logs/                   # Log files
├── src/                    # Source code
│   ├── database/           # Database management
│   ├── dify/               # Dify API integration
│   ├── drive/              # Google Drive integration
│   ├── utils/              # Utility functions
│   │   ├── config.py       # Configuration management
│   │   └── logger.py       # Logging setup
│   └── main.py             # Main application entry point
└── tests/                  # Test files
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gdrive-sync.git
   cd gdrive-sync
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy the example configuration file and edit it with your settings:
   ```
   cp config/config.yaml.example config/config.yaml
   ```

4. Edit `config/config.yaml` with your Google Drive folder ID, Dify dataset ID, and API key.

## Usage

Run the application:

```
python src/main.py
```

Additional options:
```
python src/main.py --config path/to/config.yaml --log-level DEBUG
```

## Development

This project is organized into sections as outlined in the `plan.md` file. Each section is implemented and tested before moving to the next one.
