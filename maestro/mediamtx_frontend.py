# frontend/streamlit_ui.py
"""
MediaMTX Frontend UI
Clean separation from backend - only handles UI logic and user interactions.
"""

import streamlit as st
import json
import time
from typing import List, Dict
import sys
import os

# Add backend to path (adjust as needed for your project structure)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from mediamtx_service import (
    MediaMTXBackend, 
    MediaMTXService, 
    Computer, 
    VideoPath, 
    RecordingStatus,
    create_backend
)

class MediaMTXUI:
    """Frontend UI controller - handles all UI logic"""
    
    def __init__(self):
        self.backend: MediaMTXBackend = None
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'online_computers' not in st.session_state:
            st.session_state.online_computers = []
        
        if 'backend_config' not in st.session_state:
            st.session_state.backend_config = {
                'api_port': 9997,
                'stream_port': 8888,
                'timeout': 3,
                'backend_type': 'default'
            }
        
        if 'last_scan_time' not in st.session_state:
            st.session_state.last_scan_time = None
        
        if 'ui_settings' not in st.session_state:
            st.session_state.ui_settings = {
                'admin_mode': False,
                'auto_refresh': False,
                'show_details': False
            }
    
    def _get_backend(self) -> MediaMTXBackend:
        """Get or create backend instance"""
        if self.backend is None or self._backend_config_changed():
            config = st.session_state.backend_config
            self.backend = create_backend(
                backend_type=config['backend_type'],
                api_port=config['api_port'],
                stream_port=config['stream_port'],
                timeout=config['timeout']
            )
        return self.backend
    
    def _backend_config_changed(self) -> bool:
        """Check if backend configuration has changed"""
        if self.backend is None:
            return True
        
        config = st.session_state.backend_config
        current_config = {
            'api_port': getattr(self.backend, 'api_port', None),
            'stream_port': getattr(self.backend, 'stream_port', None),
            'timeout': getattr(self.backend, 'timeout', None)
        }
        
        return (
            config['api_port'] != current_config['api_port'] or
            config['stream_port'] != current_config['stream_port'] or
            config['timeout'] != current_config['timeout']
        )
    
    def render_sidebar(self):
        """Render the sidebar configuration"""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Network Settings
            with st.expander("🌐 Network Settings", expanded=True):
                ip_range = st.text_input(
                    "IP Range",
                    value="192.168.1.0/24",
                    help="Enter IP range in CIDR notation"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.backend_config['api_port'] = st.number_input(
                        "API Port",
                        value=st.session_state.backend_config['api_port'],
                        min_value=1,
                        max_value=65535
                    )
                
                with col2:
                    st.session_state.backend_config['stream_port'] = st.number_input(
                        "Stream Port",
                        value=st.session_state.backend_config['stream_port'],
                        min_value=1,
                        max_value=65535
                    )
                
                st.session_state.backend_config['timeout'] = st.slider(
                    "Timeout (seconds)",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.backend_config['timeout']
                )
            
            # UI Settings
            with st.expander("🎛️ UI Settings"):
                st.session_state.ui_settings['admin_mode'] = st.checkbox(
                    "Admin Mode",
                    value=st.session_state.ui_settings['admin_mode'],
                    help="Enable recording controls and advanced features"
                )
                
                st.session_state.ui_settings['show_details'] = st.checkbox(
                    "Show Path Details",
                    value=st.session_state.ui_settings['show_details'],
                    help="Display detailed path information"
                )
                
                st.session_state.ui_settings['auto_refresh'] = st.checkbox(
                    "Auto Refresh (30s)",
                    value=st.session_state.ui_settings['auto_refresh'],
                    help="Automatically refresh computer status"
                )
            
            # Control Buttons
            st.subheader("🎮 Controls")
            
            col1, col2 = st.columns(2)
            with col1:
                scan_clicked = st.button("🔍 Scan Network", use_container_width=True)
            
            with col2:
                refresh_clicked = st.button("🔄 Refresh", use_container_width=True)
            
            # Handle button clicks
            if scan_clicked:
                self._scan_network(ip_range)
            
            if refresh_clicked:
                self._refresh_computers()
            
            # Status Display
            self._render_status_summary()
            
            return ip_range
    
    def _scan_network(self, ip_range: str):
        """Perform network scan"""
        backend = self._get_backend()
        
        with st.spinner(f"🔍 Scanning {ip_range}..."):
            computers = backend.discover_computers(ip_range)
            st.session_state.online_computers = computers
            st.session_state.last_scan_time = time.time()
        
        if computers:
            st.success(f"✅ Found {len(computers)} online computers")
        else:
            st.warning("⚠️ No computers found in the specified range")
    
    def _refresh_computers(self):
        """Refresh current computers"""
        if not st.session_state.online_computers:
            st.info("No computers to refresh. Scan network first.")
            return
        
        backend = self._get_backend()
        
        with st.spinner("🔄 Refreshing computers..."):
            refreshed_computers = []
            
            for computer in st.session_state.online_computers:
                updated_computer = backend.check_computer_online(computer.ip)
                if updated_computer:
                    refreshed_computers.append(updated_computer)
        
        st.session_state.online_computers = refreshed_computers
        st.success(f"✅ Refreshed {len(refreshed_computers)} computers")
    
    def _render_status_summary(self):
        """Render status summary in sidebar"""
        computers = st.session_state.online_computers
        
        if computers:
            st.subheader("📊 Status")
            st.success(f"✅ {len(computers)} computers online")
            
            # Show last scan time
            if st.session_state.last_scan_time:
                scan_time = time.strftime(
                    "%H:%M:%S",
                    time.localtime(st.session_state.last_scan_time)
                )
                st.caption(f"Last scan: {scan_time}")
            
            # Computer list
            with st.expander("💻 Online Computers"):
                for computer in computers:
                    path_count = len(computer.paths)
                    st.text(f"• {computer.ip} ({path_count} paths)")
        else:
            st.info("📡 No computers detected")
    
    def render_main_content(self):
        """Render main content area"""
        computers = st.session_state.online_computers
        
        if not computers:
            self._render_welcome_screen()
            return
        
        # Auto-refresh logic
        if st.session_state.ui_settings['auto_refresh']:
            time.sleep(0.1)  # Small delay for UI responsiveness
            if st.session_state.last_scan_time:
                time_since_scan = time.time() - st.session_state.last_scan_time
                if time_since_scan > 30:  # 30 seconds
                    self._refresh_computers()
        
        # Create tabs for computers
        tab_names = [f"💻 {comp.ip}" for comp in computers]
        tabs = st.tabs(tab_names)
        
        for tab, computer in zip(tabs, computers):
            with tab:
                self._render_computer_tab(computer)
    
    def _render_welcome_screen(self):
        """Render welcome/instruction screen"""
        st.info("📡 Welcome to MediaMTX Control Panel")
        
        st.markdown("""
        ### 🚀 Getting Started:
        
        1. **Configure Network**: Set your IP range in the sidebar (e.g., `192.168.1.0/24`)
        2. **Adjust Ports**: Set MediaMTX API port (default: 9997) and stream port (default: 8888)
        3. **Scan Network**: Click "🔍 Scan Network" to discover online computers
        4. **Control Streams**: Use the tabs to manage each computer's video streams
        
        ### 🛡️ Admin Features:
        - Enable "Admin Mode" in settings to access recording controls
        - Toggle recording for individual video paths
        - View detailed path configurations
        - Export computer configurations
        
        ### 🔧 Advanced:
        - Auto-refresh keeps computer status updated
        - Configurable timeouts for network operations
        - Resilient error handling for offline computers
        """)
        
        # Show some tips based on current state
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        
        if not st.session_state.online_computers:
            st.markdown("- Start by scanning your network to discover MediaMTX computers")
        
        if st.session_state.ui_settings['admin_mode']:
            st.markdown("- Admin mode is enabled - you'll see recording controls")
        else:
            st.markdown("- Enable Admin mode in settings for recording controls")
    
    def _render_computer_tab(self, computer: Computer):
        """Render content for a single computer tab"""
        st.subheader(f"🖥️ Computer: {computer.ip}")
        
        # Computer info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "🟢 Online")
        with col2:
            st.metric("Video Paths", len(computer.paths))
        with col3:
            last_seen = time.strftime("%H:%M:%S", time.localtime(computer.last_seen))
            st.metric("Last Seen", last_seen)
        
        if not computer.paths:
            st.warning("⚠️ No video paths found on this computer")
            return
        
        # Render video paths
        self._render_video_paths(computer)
        
        # Global computer controls
        st.divider()
        self._render_computer_controls(computer)
    
    def _render_video_paths(self, computer: Computer):
        """Render video paths for a computer"""
        st.subheader(f"📹 Video Paths ({len(computer.paths)})")
        
        # Arrange paths in columns (max 3 per row)
        num_cols = min(3, len(computer.paths))
        if num_cols > 0:
            cols = st.columns(num_cols)
            
            for idx, path in enumerate(computer.paths):
                col = cols[idx % num_cols]
                
                with col:
                    self._render_single_path(path, idx)
    
    def _render_single_path(self, path: VideoPath, idx: int):
        """Render a single video path"""
        # Path header
        st.markdown(f"**📺 {path.name}**")
        
        # Recording status indicator
        status_color = {
            RecordingStatus.RECORDING: "🔴",
            RecordingStatus.STOPPED: "⚪",
            RecordingStatus.UNKNOWN: "❓",
            RecordingStatus.ERROR: "❌"
        }
        
        status_icon = status_color.get(path.recording_status, "❓")
        st.caption(f"{status_icon} {path.recording_status.value.title()}")
        
        # Stream URL
        st.code(path.url, language="text")
        
        # Admin controls
        if st.session_state.ui_settings['admin_mode']:
            self._render_path_admin_controls(path, idx)
        
        # Path details
        if st.session_state.ui_settings['show_details']:
            with st.expander(f"🔍 Details - {path.name}"):
                if path.metadata:
                    st.json(path.metadata)
                else:
                    st.info("No metadata available")
    
    def _render_path_admin_controls(self, path: VideoPath, idx: int):
        """Render admin controls for a path"""
        st.markdown("**🛡️ Admin Controls:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            is_recording = path.recording_status == RecordingStatus.RECORDING
            button_text = "⏹️ Stop Recording" if is_recording else "🔴 Start Recording"
            
            if st.button(
                button_text,
                key=f"rec_{path.ip}_{path.name}_{idx}",
                use_container_width=True
            ):
                self._toggle_recording(path, not is_recording)
        
        with col2:
            if st.button(
                "📊 Get Stats",
                key=f"stats_{path.ip}_{path.name}_{idx}",
                use_container_width=True
            ):
                self._show_path_statistics(path)
    
    def _render_computer_controls(self, computer: Computer):
        """Render global controls for a computer"""
        st.subheader("🎛️ Computer Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"🔄 Refresh Paths", key=f"refresh_paths_{computer.ip}"):
                self._refresh_computer_paths(computer)
        
        with col2:
            if st.button(f"📋 Export Config", key=f"export_{computer.ip}"):
                self._export_computer_config(computer)
        
        with col3:
            if st.button(f"📊 System Stats", key=f"system_stats_{computer.ip}"):
                self._show_system_stats(computer)
        
        with col4:
            if st.session_state.ui_settings['admin_mode']:
                if st.button(
                    f"⚠️ Restart Service",
                    key=f"restart_{computer.ip}",
                    type="secondary"
                ):
                    self._restart_computer_service(computer)
    
    def _toggle_recording(self, path: VideoPath, enable: bool):
        """Toggle recording for a path"""
        backend = self._get_backend()
        
        with st.spinner(f"{'Starting' if enable else 'Stopping'} recording..."):
            success = backend.toggle_recording(path, enable)
        
        if success:
            action = "started" if enable else "stopped"
            st.success(f"✅ Recording {action} for {path.name}")
            # Trigger a refresh to update the UI
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(f"❌ Failed to toggle recording for {path.name}")
    
    def _show_path_statistics(self, path: VideoPath):
        """Show statistics for a path"""
        backend = self._get_backend()
        
        with st.spinner("Getting statistics..."):
            stats = backend.get_path_statistics(path)
        
        st.json(stats)
    
    def _refresh_computer_paths(self, computer: Computer):
        """Refresh paths for a specific computer"""
        backend = self._get_backend()
        
        with st.spinner(f"Refreshing paths for {computer.ip}..."):
            updated_computer = backend.check_computer_online(computer.ip)
            
            if updated_computer:
                # Update the computer in session state
                for i, comp in enumerate(st.session_state.online_computers):
                    if comp.ip == computer.ip:
                        st.session_state.online_computers[i] = updated_computer
                        break
                
                st.success(f"✅ Refreshed {len(updated_computer.paths)} paths")
                st.rerun()
            else:
                st.error(f"❌ Computer {computer.ip} is no longer accessible")
    
    def _export_computer_config(self, computer: Computer):
        """Export computer configuration"""
        config_data = {
            "computer_ip": computer.ip,
            "status": computer.status,
            "last_seen": computer.last_seen,
            "paths": [
                {
                    "name": path.name,
                    "url": path.url,
                    "recording_status": path.recording_status.value,
                    "metadata": path.metadata
                }
                for path in computer.paths
            ],
            "config": computer.config,
            "export_timestamp": time.time()
        }
        
        config_json = json.dumps(config_data, indent=2, default=str)
        
        st.download_button(
            "💾 Download Configuration",
            data=config_json,
            file_name=f"mediamtx_config_{computer.ip}_{int(time.time())}.json",
            mime="application/json",
            key=f"download_config_{computer.ip}"
        )
    
    def _show_system_stats(self, computer: Computer):
        """Show system statistics for a computer"""
        with st.expander(f"📊 System Statistics - {computer.ip}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Paths", len(computer.paths))
                
                recording_count = sum(
                    1 for path in computer.paths 
                    if path.recording_status == RecordingStatus.RECORDING
                )
                st.metric("Recording Paths", recording_count)
            
            with col2:
                st.metric("Computer Status", computer.status.upper())
                
                if computer.last_seen:
                    uptime = time.time() - computer.last_seen
                    st.metric("Response Time", f"{uptime:.2f}s ago")
            
            # Show path status breakdown
            if computer.paths:
                st.subheader("📹 Path Status Breakdown")
                
                status_counts = {}
                for path in computer.paths:
                    status = path.recording_status.value
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    st.write(f"• {status.title()}: {count} paths")
    
    def _restart_computer_service(self, computer: Computer):
        """Restart MediaMTX service on a computer"""
        # Show confirmation dialog
        if st.button(
            f"⚠️ Confirm Restart for {computer.ip}",
            key=f"confirm_restart_{computer.ip}",
            type="primary"
        ):
            backend = self._get_backend()
            
            with st.spinner(f"Restarting MediaMTX service on {computer.ip}..."):
                success = backend.restart_service(computer)
            
            if success:
                st.success(f"✅ Service restarted successfully on {computer.ip}")
                # Wait a bit for service to come back up
                time.sleep(2)
                self._refresh_computer_paths(computer)
            else:
                st.error(f"❌ Failed to restart service on {computer.ip}")
        else:
            st.warning("Click 'Confirm Restart' to proceed with service restart")
    
    def run(self):
        """Main UI entry point"""
        # Page configuration
        st.set_page_config(
            page_title="MediaMTX Control Panel",
            page_icon="🎥",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Header
        st.title("🎥 MediaMTX Computer Control Panel")
        st.markdown("---")
        
        # Render UI components
        self.render_sidebar()
        self.render_main_content()
        
        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.caption(
                "MediaMTX Control Panel | "
                f"Backend: {st.session_state.backend_config['backend_type']} | "
                f"API Port: {st.session_state.backend_config['api_port']}"
            )

def main():
    """Application entry point"""
    ui = MediaMTXUI()
    ui.run()

if __name__ == "__main__":
    main()