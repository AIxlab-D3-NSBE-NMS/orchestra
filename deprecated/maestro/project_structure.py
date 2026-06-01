# config/settings.py
"""
Configuration settings for MediaMTX Control Panel
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class MediaMTXConfig:
    """MediaMTX backend configuration"""
    api_port: int = 9997
    stream_port: int = 8888
    timeout: int = 3
    max_workers: int = 50
    cache_ttl: int = 30

@dataclass
class UIConfig:
    """UI configuration"""
    page_title: str = "MediaMTX Control Panel"
    page_icon: str = "🎥"
    layout: str = "wide"
    default_ip_range: str = "192.168.10.0/24"
    admin_mode_default: bool = False
    auto_refresh_default: bool = False
    show_details_default: bool = False

@dataclass
class AppConfig:
    """Application configuration"""
    mediamtx: MediaMTXConfig
    ui: UIConfig
    debug: bool = False
    
    @classmethod
    def load_default(cls) -> 'AppConfig':
        """Load default configuration"""
        return cls(
            mediamtx=MediaMTXConfig(),
            ui=UIConfig(),
            debug=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'mediamtx': {
                'api_port': self.mediamtx.api_port,
                'stream_port': self.mediamtx.stream_port,
                'timeout': self.mediamtx.timeout,
                'max_workers': self.mediamtx.max_workers,
                'cache_ttl': self.mediamtx.cache_ttl
            },
            'ui': {
                'page_title': self.ui.page_title,
                'page_icon': self.ui.page_icon,
                'layout': self.ui.layout,
                'default_ip_range': self.ui.default_ip_range,
                'admin_mode_default': self.ui.admin_mode_default,
                'auto_refresh_default': self.ui.auto_refresh_default,
                'show_details_default': self.ui.show_details_default
            },
            'debug': self.debug
        }

# main.py
"""
Main entry point for MediaMTX Control Panel
"""

import streamlit as st
import sys
import os
import logging

# Add project directories to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([
    os.path.join(project_root, 'backend'),
    os.path.join(project_root, 'frontend'),
    os.path.join(project_root, 'config')
])

try:
    from streamlit_ui import MediaMTXUI
    from settings import AppConfig
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def main():
        """Application entry point"""
        # Load configuration
        config = AppConfig.load_default()
        
        # Enable debug mode if needed
        if config.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Initialize and run UI
        ui = MediaMTXUI()
        ui.run()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Please ensure all required files are in the correct directories:")
    st.code("""
    Project Structure:
    ├── main.py                 # Main entry point
    ├── backend/
    │   └── mediamtx_service.py # Backend service
    ├── frontend/
    │   └── streamlit_ui.py     # Frontend UI
    ├── config/
    │   └── settings.py         # Configuration
    └── requirements.txt        # Dependencies
    """)

# requirements.txt
"""
streamlit>=1.28.0
requests>=2.31.0
"""

# README.md
"""
# MediaMTX Control Panel

A Streamlit-based web interface for controlling multiple MediaMTX instances across your network.

## Features

- **Network Discovery**: Automatically scan IP ranges to find online MediaMTX computers
- **Multi-Computer Control**: Tabbed interface for managing multiple computers simultaneously
- **Flexible Video Sources**: Dynamically detects and displays all available video streams
- **Recording Management**: Admin controls for starting/stopping recordings per stream
- **Resilient Architecture**: Handles offline computers gracefully without errors
- **Real-time Updates**: Auto-refresh capabilities and manual refresh options
- **Configuration Export**: Download computer configurations as JSON files

## Project Structure

```
mediamtx-control/
├── main.py                    # Application entry point
├── backend/
│   └── mediamtx_service.py   # Backend service with MediaMTX API integration
├── frontend/
│   └── streamlit_ui.py       # Clean Streamlit UI frontend
├── config/
│   └── settings.py           # Configuration management
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Installation

1. **Clone or create the project structure**:
   ```bash
   mkdir mediamtx-control
   cd mediamtx-control
   mkdir backend frontend config
   ```

2. **Install dependencies**:
   ```bash
   pip install streamlit requests
   ```

3. **Copy the provided code files** into their respective directories

4. **Run the application**:
   ```bash
   streamlit run main.py
   ```

## Usage

### Basic Setup
1. **Configure Network**: Set your IP range in the sidebar (e.g., `192.168.1.0/24`)
2. **Set Ports**: Configure MediaMTX API port (default: 9997) and stream port (default: 8888)
3. **Scan Network**: Click "🔍 Scan Network" to discover online computers
4. **Manage Streams**: Use tabs to control each computer's video streams

### Admin Features
- Enable "Admin Mode" in settings to access:
  - Recording start/stop controls
  - System statistics
  - Service restart capabilities
  - Path statistics and details

### Advanced Configuration
- **Auto-refresh**: Automatically update computer status every 30 seconds
- **Timeout Settings**: Adjust network timeout for slow connections
- **Show Details**: Display detailed path metadata and configurations

## Backend Architecture

The backend (`mediamtx_service.py`) provides a clean abstraction layer:

- **Abstract Base Class**: `MediaMTXBackend` defines the interface
- **Default Implementation**: `MediaMTXService` handles MediaMTX API calls
- **Extensible Design**: Easy to add new backends (e.g., different APIs, mock services)
- **Caching System**: Reduces redundant API calls with configurable TTL
- **Error Handling**: Robust error handling with proper logging

### Key Backend Classes:
- `Computer`: Represents a network computer with MediaMTX
- `VideoPath`: Represents individual video streams/paths
- `RecordingStatus`: Enum for recording states
- `MediaMTXService`: Main backend implementation

## Frontend Architecture

The frontend (`streamlit_ui.py`) focuses purely on UI logic:

- **Clean Separation**: No direct API calls, uses backend abstraction
- **Session State Management**: Proper Streamlit state handling
- **Component-Based**: Modular UI components for easy maintenance
- **Responsive Design**: Adapts to different numbers of computers/streams
- **User Experience**: Intuitive controls with clear status indicators

## Extending the System

### Adding New Backend Features
1. Extend the `MediaMTXBackend` abstract class
2. Implement new methods in `MediaMTXService`
3. UI automatically benefits from new functionality

### Custom Backend Implementation
```python
class MyCustomBackend(MediaMTXBackend):
    def discover_computers(self, ip_range: str) -> List[Computer]:
        # Your custom implementation
        pass
    
    # Implement other abstract methods...

# Use with factory function
backend = create_backend("custom", **config)
```

### UI Customization
- Modify `UIConfig` in `settings.py` for appearance changes
- Add new UI components in `MediaMTXUI` class methods
- Extend session state for new features

## API Endpoints Used

The system interacts with MediaMTX API endpoints:
- `GET /v3/config/global/get` - Check computer status and config
- `GET /v3/paths/list` - List all video paths
- `GET /v3/recordings/list` - Get recording status
- `POST /v3/recordings/start` - Start recording
- `POST /v3/recordings/stop` - Stop recording
- `GET /v3/paths/get/{path}` - Get path statistics

## Troubleshooting

### Common Issues:
1. **No computers found**: Check IP range and ensure MediaMTX is running
2. **Connection timeouts**: Increase timeout in sidebar settings
3. **Import errors**: Verify all files are in correct directories
4. **Recording issues**: Ensure paths support recording in MediaMTX config

### Debug Mode:
Set `debug=True` in `AppConfig` for detailed logging.

## License

This project is open source. Feel free to modify and distribute according to your needs.
"""
