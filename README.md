# Google Drive Sync and Dify API Integration

This application monitors a Google Drive folder (and its subfolders) for new or modified files and pushes them to the Dify API. It provides real-time synchronization between your Google Drive content and Dify datasets.

## Features

- **Automatic File Monitoring**: Tracks new, modified, and deleted files in Google Drive
- **Recursive Folder Support**: Monitors all subfolders within the specified root folder
- **Secure Authentication**: Uses Google Drive service account for secure, server-side authentication
- **Efficient Change Detection**: Only processes files that have changed since the last check
- **Robust Error Handling**: Gracefully handles API errors and connection issues
- **Configurable Polling**: Adjustable polling interval to balance responsiveness and API usage
- **Thread-Safe Database**: SQLite database for tracking file metadata across multiple threads

## Project Structure

```
gdrive-sync/
├── config/                 # Configuration files
│   └── config.yaml.example # Example configuration file
├── data/                   # Database and temporary files
├── docs/                   # Documentation
│   └── service_account_setup.md # Service account setup guide
├── logs/                   # Log files
├── src/                    # Source code
│   ├── database/           # Database management
│   │   └── db_manager.py   # Thread-safe database manager
│   ├── dify/               # Dify API integration
│   ├── drive/              # Google Drive integration
│   │   ├── change_detector.py    # File change detection
│   │   ├── polling_system.py     # Polling system
│   │   ├── service_auth.py       # Service account authentication
│   │   └── service_drive_client.py # Google Drive client
│   ├── utils/              # Utility functions
│   │   ├── config.py       # Configuration management
│   │   └── logger.py       # Logging setup
│   └── main.py             # Main application entry point
└── tests/                  # Test files
    ├── test_drive.py       # Test Google Drive connectivity
    └── test_change_detection.py # Test file change detection
```

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account with Drive API enabled
- Google Drive service account with appropriate permissions
- Dify API access (for the upload functionality)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/gdrive-sync.git
cd gdrive-sync
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up a Google Drive service account

- Follow the detailed instructions in `docs/service_account_setup.md`
- Download the service account key file to a secure location
- Share your target Google Drive folder with the service account email

### 4. Configure the application

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` with your settings:

```yaml
# Google Drive settings
google_drive:
  # Path to the service account key file
  service_account_file: "path/to/your-service-account-key.json"
  
  # The ID of the folder to monitor (from the Google Drive URL)
  folder_id: "your_folder_id_here"
  
  # Polling interval in seconds
  polling_interval: 300  # 5 minutes

# Dify API settings
dify:
  # API endpoint
  api_url: "https://api.dify.ai/v1/datasets/{dataset_id}/document/create-by-file"
  # Your dataset ID
  dataset_id: "your_dataset_id_here"
  # Your API key
  api_key: "your_api_key_here"

# Database settings
database:
  # Path to the SQLite database file
  path: "data/file_metadata.db"
```

## Usage

### Running the application

Start the continuous monitoring service:

```bash
python src/main.py
```

The application will run in the foreground, monitoring for changes at the configured interval. Press `Ctrl+C` to stop.

### Command-line options

```bash
# Use a different configuration file
python src/main.py --config path/to/config.yaml

# Set a different log level
python src/main.py --log-level DEBUG

# Run a single polling cycle and exit
python src/main.py --poll-now
```

### Testing

Test Google Drive connectivity and file listing:

```bash
python test_drive.py
```

Test the file change detection system:

```bash
python test_change_detection.py
```

## Development

This project follows a modular architecture with clear separation of concerns:

1. **Configuration Management**: Handles loading and accessing configuration settings
2. **Google Drive Integration**: Manages authentication and file operations with Google Drive
3. **Change Detection**: Identifies new, modified, and deleted files
4. **Database Management**: Tracks file metadata for efficient change detection
5. **Polling System**: Schedules and executes periodic checks for changes
6. **Dify API Integration**: Uploads files to the Dify API

Refer to `plan.md` for the detailed implementation roadmap.

## Troubleshooting

### Common Issues

- **Authentication Errors**: Verify your service account key file is correct and the service account has access to the folder
- **Database Errors**: Check file permissions for the database directory
- **API Rate Limits**: Adjust the polling interval if you encounter Google API rate limiting

### Logs

Check the logs for detailed error information:

```bash
tail -f logs/gdrive_sync.log
```

On Windows:

```powershell
Get-Content -Path logs/gdrive_sync.log -Wait
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

