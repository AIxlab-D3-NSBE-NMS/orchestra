# backend/mediamtx_service.py
"""
MediaMTX Backend Service
Provides abstracted interface for computer discovery and control operations.
"""

import requests
import ipaddress
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import List, Dict, Set, Optional, Tuple
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecordingStatus(Enum):
    STOPPED = "stopped"
    RECORDING = "recording"
    UNKNOWN = "unknown"
    ERROR = "error"

@dataclass
class VideoPath:
    """Represents a video path/stream on a computer"""
    name: str
    ip: str
    url: str
    recording_status: RecordingStatus = RecordingStatus.UNKNOWN
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Computer:
    """Represents a computer in the network"""
    ip: str
    status: str
    config: Dict = None
    paths: List[VideoPath] = None
    last_seen: float = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.paths is None:
            self.paths = []
        if self.last_seen is None:
            self.last_seen = time.time()

class MediaMTXBackend(ABC):
    """Abstract base class for MediaMTX backend implementations"""
    
    @abstractmethod
    def discover_computers(self, ip_range: str) -> List[Computer]:
        """Discover computers in the given IP range"""
        pass
    
    @abstractmethod
    def check_computer_online(self, ip: str) -> Optional[Computer]:
        """Check if a specific computer is online"""
        pass
    
    @abstractmethod
    def get_computer_paths(self, computer: Computer) -> List[VideoPath]:
        """Get all video paths for a computer"""
        pass
    
    @abstractmethod
    def toggle_recording(self, path: VideoPath, enable: bool) -> bool:
        """Toggle recording for a video path"""
        pass
    
    @abstractmethod
    def get_recording_status(self, path: VideoPath) -> RecordingStatus:
        """Get current recording status for a path"""
        pass
    
    @abstractmethod
    def restart_service(self, computer: Computer) -> bool:
        """Restart MediaMTX service on a computer"""
        pass
    
    @abstractmethod
    def get_path_statistics(self, path: VideoPath) -> Dict:
        """Get statistics for a video path"""
        pass

class MediaMTXService(MediaMTXBackend):
    """Default implementation of MediaMTX backend"""
    
    def __init__(self, 
                 api_port: int = 9997, 
                 stream_port: int = 8888,
                 timeout: int = 3,
                 max_workers: int = 50):
        self.api_port = api_port
        self.stream_port = stream_port
        self.timeout = timeout
        self.max_workers = max_workers
        self._computer_cache = {}
        self._cache_ttl = 30  # seconds
    
    def discover_computers(self, ip_range: str) -> List[Computer]:
        """Discover computers in the given IP range"""
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            online_computers = []
            
            logger.info(f"Scanning {network.num_addresses} addresses in {ip_range}")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.check_computer_online, str(ip)): ip 
                    for ip in network.hosts()
                }
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        online_computers.append(result)
                        # Update cache
                        self._computer_cache[result.ip] = {
                            'computer': result,
                            'timestamp': time.time()
                        }
            
            logger.info(f"Found {len(online_computers)} online computers")
            return sorted(online_computers, key=lambda x: ipaddress.ip_address(x.ip))
            
        except Exception as e:
            logger.error(f"Error discovering computers in range {ip_range}: {e}")
            return []
    
    def check_computer_online(self, ip: str) -> Optional[Computer]:
        """Check if a specific computer is online"""
        # Check cache first
        if ip in self._computer_cache:
            cache_entry = self._computer_cache[ip]
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                return cache_entry['computer']
        
        try:
            url = f"http://{ip}:{self.api_port}/v3/config/global/get"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                computer = Computer(
                    ip=ip,
                    status="online",
                    config=response.json(),
                    last_seen=time.time()
                )
                
                # Get paths for this computer
                computer.paths = self.get_computer_paths(computer)
                
                return computer
            
            return None
            
        except Exception as e:
            logger.debug(f"Computer {ip} offline or unreachable: {e}")
            return None
    
    def get_computer_paths(self, computer: Computer) -> List[VideoPath]:
        """Get all video paths for a computer"""
        try:
            url = f"http://{computer.ip}:{self.api_port}/v3/paths/list"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get paths from {computer.ip}: {response.status_code}")
                return []
            
            data = response.json()
            paths_data = data.get("items", [])
            
            paths = []
            for path_info in paths_data:
                path_name = path_info.get('name', 'unknown')
                
                path = VideoPath(
                    name=path_name,
                    ip=computer.ip,
                    url=self._generate_stream_url(computer.ip, path_name),
                    metadata=path_info
                )
                
                # Get recording status
                path.recording_status = self.get_recording_status(path)
                paths.append(path)
            
            logger.debug(f"Found {len(paths)} paths on {computer.ip}")
            return paths
            
        except Exception as e:
            logger.error(f"Error getting paths from {computer.ip}: {e}")
            return []
    
    def toggle_recording(self, path: VideoPath, enable: bool) -> bool:
        """Toggle recording for a video path"""
        try:
            action = "start" if enable else "stop"
            url = f"http://{path.ip}:{self.api_port}/v3/recordings/{action}"
            payload = {"path": path.name}
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            success = response.status_code == 200
            
            if success:
                # Update the path's recording status
                path.recording_status = RecordingStatus.RECORDING if enable else RecordingStatus.STOPPED
                logger.info(f"Successfully {'started' if enable else 'stopped'} recording for {path.ip}/{path.name}")
            else:
                logger.error(f"Failed to toggle recording for {path.ip}/{path.name}: {response.status_code}")
                path.recording_status = RecordingStatus.ERROR
            
            return success
            
        except Exception as e:
            logger.error(f"Error toggling recording for {path.ip}/{path.name}: {e}")
            path.recording_status = RecordingStatus.ERROR
            return False
    
    def get_recording_status(self, path: VideoPath) -> RecordingStatus:
        """Get current recording status for a path"""
        try:
            url = f"http://{path.ip}:{self.api_port}/v3/recordings/list"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code != 200:
                return RecordingStatus.UNKNOWN
            
            data = response.json()
            recordings = data.get("items", [])
            
            # Check if this path is currently being recorded
            for recording in recordings:
                if recording.get("path") == path.name:
                    return RecordingStatus.RECORDING
            
            return RecordingStatus.STOPPED
            
        except Exception as e:
            logger.debug(f"Error getting recording status for {path.ip}/{path.name}: {e}")
            return RecordingStatus.UNKNOWN
    
    def restart_service(self, computer: Computer) -> bool:
        """Restart MediaMTX service on a computer"""
        try:
            # This would depend on your specific setup
            # Could be a custom API endpoint or system command
            url = f"http://{computer.ip}:{self.api_port}/v3/config/global/restart"
            response = requests.post(url, timeout=self.timeout * 2)
            
            success = response.status_code == 200
            if success:
                logger.info(f"Successfully restarted MediaMTX on {computer.ip}")
            else:
                logger.error(f"Failed to restart MediaMTX on {computer.ip}: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error restarting service on {computer.ip}: {e}")
            return False
    
    def get_path_statistics(self, path: VideoPath) -> Dict:
        """Get statistics for a video path"""
        try:
            url = f"http://{path.ip}:{self.api_port}/v3/paths/get/{path.name}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            
            return {"error": f"Failed to get statistics: {response.status_code}"}
            
        except Exception as e:
            logger.error(f"Error getting statistics for {path.ip}/{path.name}: {e}")
            return {"error": str(e)}
    
    def _generate_stream_url(self, ip: str, path_name: str) -> str:
        """Generate stream URL for a path"""
        return f"http://{ip}:{self.stream_port}/{path_name}"
    
    def update_configuration(self, api_port: int = None, stream_port: int = None, 
                           timeout: int = None, max_workers: int = None):
        """Update service configuration"""
        if api_port is not None:
            self.api_port = api_port
        if stream_port is not None:
            self.stream_port = stream_port
        if timeout is not None:
            self.timeout = timeout
        if max_workers is not None:
            self.max_workers = max_workers
        
        # Clear cache when configuration changes
        self._computer_cache.clear()
        logger.info("Backend configuration updated")
    
    def get_cached_computers(self) -> List[Computer]:
        """Get computers from cache (useful for quick refreshes)"""
        current_time = time.time()
        valid_computers = []
        
        for ip, cache_entry in self._computer_cache.items():
            if current_time - cache_entry['timestamp'] < self._cache_ttl:
                valid_computers.append(cache_entry['computer'])
        
        return sorted(valid_computers, key=lambda x: ipaddress.ip_address(x.ip))
    
    def clear_cache(self):
        """Clear the computer cache"""
        self._computer_cache.clear()
        logger.info("Computer cache cleared")

# Factory function for creating backend instances
def create_backend(backend_type: str = "default", **kwargs) -> MediaMTXBackend:
    """Factory function to create backend instances"""
    if backend_type == "default":
        return MediaMTXService(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

# Example of how to extend the backend for different implementations
class MockMediaMTXService(MediaMTXBackend):
    """Mock implementation for testing"""
    
    def __init__(self):
        self.mock_computers = []
        self.mock_recording_states = {}
    
    def discover_computers(self, ip_range: str) -> List[Computer]:
        # Return mock data for testing
        return self.mock_computers
    
    def check_computer_online(self, ip: str) -> Optional[Computer]:
        for comp in self.mock_computers:
            if comp.ip == ip:
                return comp
        return None
    
    def get_computer_paths(self, computer: Computer) -> List[VideoPath]:
        return computer.paths
    
    def toggle_recording(self, path: VideoPath, enable: bool) -> bool:
        key = f"{path.ip}_{path.name}"
        self.mock_recording_states[key] = enable
        path.recording_status = RecordingStatus.RECORDING if enable else RecordingStatus.STOPPED
        return True
    
    def get_recording_status(self, path: VideoPath) -> RecordingStatus:
        key = f"{path.ip}_{path.name}"
        if self.mock_recording_states.get(key, False):
            return RecordingStatus.RECORDING
        return RecordingStatus.STOPPED
    
    def restart_service(self, computer: Computer) -> bool:
        return True
    
    def get_path_statistics(self, path: VideoPath) -> Dict:
        return {"mock": "statistics"}
