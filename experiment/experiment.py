
from selenium import webdriver  # to control the browser
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
import selenium.common.exceptions
import time, threading
import subprocess
import requests

class MediaMTX:
    @staticmethod
    def start_mediamtx(config_path):
        proc = subprocess.Popen(
            ["mediamtx", config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Started mediamtx with PID {proc.pid}")
        return proc

    @staticmethod
    def set_path_record_status(ip_address, path_name, enable, port=9997, timeout=2):
        payload = {"record": bool(enable)}
        try:
            r = requests.patch(
                f"http://{ip_address}:{port}/v3/config/paths/patch/{path_name}",
                json=payload,
                timeout=timeout,
            )
            print(f"Set record={enable} for path '{path_name}': {r.status_code} {r.text}")
            return r.ok
        except requests.exceptions.RequestException as e:
            print(f"Failed to request: {e}")
            return False

    @staticmethod
    def start_recording(path_name="screen", ip_address="localhost", port=9997, timeout=2):
        return MediaMTX.set_path_record_status(ip_address, path_name, True, port, timeout)

    @staticmethod
    def stop_recording(path_name="screen", ip_address="localhost", port=9997, timeout=2):
        return MediaMTX.set_path_record_status(ip_address, path_name, False, port, timeout)


class Task:
    """A task that runs when triggered and completes based on some condition."""
    def __init__(self):
        self.status = "IDLE"  # IDLE -> RUNNING -> COMPLETED
        self.window = None
    def is_triggered(self, previous_task):
        """Check if this task should start. Override in subclasses."""
        return False
    def start(self):
        """Start the task. Override in subclasses."""
        self.status = "RUNNING"
    def is_complete(self):
        """Check if task is done. Override in subclasses."""
        return False
    def cleanup(self):
        """Close window if needed. Override to keep window open."""
        if self.window:
            self.window.quit()
            self.window = None

class ChromiumHandler():
    DEFAULT_CHECK_INTERVAL = 0.5 # every 0.5 seconds checks for callback / clicks
    def __init__(self):
        self.browser        = None # driver
        self.service        = None
        self.options        = None
        self.monitoring     = False
        self.monitor_thread = None
        self.callbacks      = {}  # event_name: callback_function
    def create_new_window(self):
        self.service    = ChromeService("/usr/bin/chromedriver")
        self.options    = ChromeOptions()
        # important: the following line suppresses the google chromium banner
        # saying that the browser is being controlled externally
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("prefs", {
                    "profile.default_content_setting_values.notifications": 1,  # 1=allow, 2=block, 0=ask
                    "profile.managed_default_content_settings.notifications": 1})
        self.browser = webdriver.Chrome(service=self.service, options=self.options)
        # self.browser is the important 'output'
    def open_url(self, url):
        self.browser.get(url)
    def register_callback(self, event_name, callback_function):
        """Register a callback for a specific event (e.g., 'page_contains', 'url_changed')"""
        self.callbacks[event_name] = callback_function
    def start_monitoring(self, check_interval=DEFAULT_CHECK_INTERVAL):
        """Start background monitoring thread"""
        if self.monitoring:
            return
        self.monitoring = True

        def monitor_loop():
            while self.monitoring and self.browser:
                try:
                    # Check for registered callbacks
                    for event_name, callback in self.callbacks.items():
                        callback(self.browser)
                    time.sleep(check_interval)
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    break

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
    def check_page_content(self, keyword):
        """Helper method to check if page contains specific content"""
        if self.browser:
            return keyword in self.browser.page_source
        return False
    def wait_for_element_click(self, locator, timeout=10, click_detection_method="data-attribute", data_attribute="data-clicked"):
        """
        General function to wait for any element to be clicked

        Args:
            locator: Tuple of (By.TYPE, "selector") e.g., (By.ID, "startBtn")
            timeout: Maximum time to wait in seconds
            click_detection_method: How to detect the click ("data-attribute", "disabled", "navigation", "custom")
            data_attribute: Name of data attribute to check (for "data-attribute" method)

        Returns:
            bool: True if click detected, False if timeout/error
        """
        try:
            print(f"Waiting for user to click element: {locator}")

            if click_detection_method == "data-attribute":
                # Wait for data attribute to be set
                WebDriverWait(self.browser, timeout).until(
                    lambda driver: driver.find_element(*locator)
                                    .get_attribute(data_attribute) == "true"
                )

            elif click_detection_method == "disabled":
                # Wait for element to become disabled
                WebDriverWait(self.browser, timeout).until_not(
                    EC.element_to_be_clickable(locator)
                )

            elif click_detection_method == "navigation":
                # Wait for URL change
                current_url = self.browser.current_url
                WebDriverWait(self.browser, timeout).until(
                    lambda driver: driver.current_url != current_url
                )

            print("Element click detected!")
            return True

        except Exception as e:
            print(f"Timeout or error waiting for element click: {e}")
            return False
    def wait_for_actual_click(self, locator, timeout=3000):
        """Wait for actual click event using JavaScript listener"""
        try:
            print(f"Waiting for element to be ready: {locator}")

            # Wait for element to be present (but maybe not enabled yet)
            element = WebDriverWait(self.browser, 30).until(
                EC.presence_of_element_located(locator)
            )

            # Add JavaScript click listener
            self.browser.execute_script("""
                const element = arguments[0];
                window.submitClicked = false;
                element.addEventListener('click', function(e) {
                    console.log('Submit button clicked!');
                    window.submitClicked = true;
                });
            """, element)

            print("Click listener added. Waiting for user to click submit...")

            # Wait for the click to be detected
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.execute_script("return window.submitClicked === true;")
            )

            print("Submit button click detected!")
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False
    def quit(self):
        """Clean shutdown of browser and monitoring"""
        self.stop_monitoring()
        if self.browser:
            self.browser.quit()
            self.browser = None
    def is_browser_open(self):
            try:
                _ = self.browser.current_url
                return True
            except selenium.common.exceptions.WebDriverException:
                return False

class WelcomePageTask(Task):
    """Shows a welcome page. Stays open so user can refer back to it."""
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.browser_handler = ChromiumHandler()
    def start(self):
        super().start()# update status to 'RUNNING'
        self.browser_handler.create_new_window()
        self.browser_handler.open_url(self.url)
    def wait_for_start_click(self, timeout=10):
        """Wait for Start button to become disabled (indicating it was clicked)"""
        if self.status == "RUNNING":
            try:
                print("Waiting for user to click Start button...")

                # Wait for button to become non-clickable (disabled)
                WebDriverWait(self.browser_handler.browser, timeout).until(
                                lambda driver: driver.find_element(By.TAG_NAME, "body")
                                              .get_attribute("data-start-clicked") == "true"
                            )
                print("Start button clicked!")
                # self.start_clicked = True
                self.status = "COMPLETED"
                return True
            finally:
                self.wait_for_start_click()
        if self.status == "COMPLETED":
            self.cleanup()

    def cleanup(self):
        # Don't close the window - let user refer back to instructions
        print("WelcomePageTask staying open for reference")
        self.browser_handler.stop_monitoring()
        # Note: not calling browser.quit() to keep window open

class WebPage(Task):
    """Shows a welcome page. Stays open so user can refer back to it."""
    def __init__(self, url, browser_handler = None):
        super().__init__()
        self.url = url
        self.browser_handler = browser_handler or self.browser_handler.create_new_window()
    def start(self):
        super().start()# update status to 'RUNNING'
        self.browser_handler.open_url(self.url)
    def wait_for_start_click(self, timeout=10):
        """Wait for Start button to become disabled (indicating it was clicked)"""
        if self.status == "RUNNING":
            try:
                print("Waiting for user to click Start button...")

                # Wait for button to become non-clickable (disabled)
                WebDriverWait(self.browser_handler.browser, timeout).until(
                                lambda driver: driver.find_element(By.TAG_NAME, "body")
                                              .get_attribute("data-start-clicked") == "true"
                            )
                print("Start button clicked!")
                # self.start_clicked = True
                self.status = "COMPLETED"
                return True
            finally:
                self.wait_for_start_click()
        if self.status == "COMPLETED":
            self.cleanup()

    def force_tab_active(self):
        """
        Force the browser window and current tab to be active/focused
        This ensures notifications will be visible to the user
        """
        try:
            # Bring browser window to front and focus
            self.browser_handler.browser.switch_to.window(self.browser_handler.browser.current_window_handle)

            # Execute JavaScript to focus the window and tab
            focus_script = """
            window.focus();
            if (window.top) {
                window.top.focus();
            }
            if (document.hasFocus && !document.hasFocus()) {
                window.focus();
            }
            window.scrollTo(0, 0);
            console.log('Window focused and brought to front');
            return true;
            """

            self.browser_handler.browser.execute_script(focus_script)
            print("Tab forced to active")
            return True

        except Exception as e:
            print(f"Error forcing tab active: {e}")
            return False

    def setup_browser_notifications(self):
        """
        Check notification support and permission status.
        Permission should already be granted via Chrome options.
        """
        script = """
        if ('Notification' in window) {
            console.log('Notification permission:', Notification.permission);
            return {
                supported: true,
                permission: Notification.permission
            };
        } else {
            return {
                supported: false,
                permission: 'not-supported'
            };
        }
        """
        try:
            result = self.browser_handler.browser.execute_script(script)
            print(f"Notification status: {result}")
            return result
        except Exception as e:
            print(f"Error checking notification status: {e}")
            return {'supported': False, 'permission': 'error'}

    def show_browser_notification(self, title, message, duration_ms=10000, icon=None):
        """
        Show a system-level browser notification that appears even when user is in another tab
        Permission should already be granted via Chrome options.

        Args:
            title (str): Notification title
            message (str): Notification body text
            duration_ms (int): How long to show notification in milliseconds
            icon (str): Optional icon URL or data URI

        Returns:
            bool: True if notification was sent, False if failed
        """
        # Escape strings to prevent JavaScript injection/errors
        title_escaped = title.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        message_escaped = message.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')

        if not icon:
            # Use a simple warning emoji or Unicode character as icon
            # This avoids SVG parsing issues entirely
            icon_option = ""
        else:
            icon_option = f", icon: '{icon}'"

        script = f"""
        (function() {{
            if ('Notification' in window) {{
                try {{
                    console.log('Current permission:', Notification.permission);

                    var notification = new Notification('{title_escaped}', {{
                        body: '{message_escaped}',
                        requireInteraction: false,
                        silent: false,
                        tag: 'experiment-notification'{icon_option}
                    }});

                    // Auto-close after duration
                    setTimeout(function() {{
                        notification.close();
                    }}, {duration_ms});

                    // Focus window when notification is clicked
                    notification.onclick = function() {{
                        window.focus();
                        this.close();
                    }};

                    console.log('Notification created successfully');
                    return true;

                }} catch (e) {{
                    console.error('Notification error:', e);
                    console.log('Error details:', e.message);
                    console.log('Permission status:', Notification.permission);
                    return false;
                }}
            }} else {{
                console.log('Notifications not supported');
                return false;
            }}
        }})();
        """

        try:
            result = self.browser_handler.browser.execute_script(script)
            if result:
                print(f"Browser notification sent: {title}")
            else:
                print(f"Browser notification failed: {title}")
            return bool(result)
        except Exception as e:
            print(f"Error showing browser notification: {e}")
            return False

    def wait_for_element_click(self, locator, timeout=10, detection_method="data-attribute", **kwargs):
            """Wait for any element to be clicked using the general function"""
            if self.status != "RUNNING":
                return False

            success = self.browser_handler.wait_for_element_click(
                locator, timeout, detection_method, **kwargs
            )

            if success:
                self.status = "COMPLETED"
                return True
            return False

    def monitor_for_target_text(self, target_text, check_interval=2, timeout=99999):
        """
        Periodically check if the page contains the target URL
        Returns the timestamp when found, or None if timeout reached
        """
        start_monitoring = time.time()
        print(f"Starting to monitor for: {target_text}")

        while time.time() - start_monitoring < timeout:
            try:
                if self.browser_handler.check_page_content(target_text):
                    print(f"Found target URL: {target_text}")
                    return time.time()
                time.sleep(check_interval)
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(check_interval)

        print(f"Timeout reached ({timeout}s) - target text not found")
        return None

    def show_non_blocking_popup(self, message, duration_seconds=5):
        """Show a custom popup that doesn't block Selenium"""
        popup_script = f"""
        var popup = document.createElement('div');
        popup.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #404040;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 96px;
            font-weight: bold;
        `;
        popup.textContent = '{message}';
        document.body.appendChild(popup);

        setTimeout(function() {{
            if (popup && popup.parentNode) {{
                popup.parentNode.removeChild(popup);
            }}
        }}, {duration_seconds * 1000});
        """
        self.browser_handler.browser.execute_script(popup_script)

    def cleanup(self):
        # Don't close the window - let user refer back to instructions
        print("WelcomePageTask staying open for reference")
        self.browser_handler.stop_monitoring()
        # Note: not calling browser.quit() to keep window open

class ScreenRecorder:
    """
    FFmpeg-based screen recorder helper.

    Usage:
      rec = ScreenRecorder()
      rec.start_recording(output_path="/tmp/screen.mkv", display=":0.0",
                          video_size="3840x2400", framerate=60)
      ...
      rec.stop_recording(timeout=15)  # graceful (sends 'q' or SIGINT)
      # If still alive:
      rec.force_stop()

    Important:
      - start_recording() is non-blocking: it launches ffmpeg and returns immediately.
      - stop_recording() blocks while waiting for ffmpeg to finalize (up to `timeout`).
      - stdout/stderr are redirected to DEVNULL to avoid pipe blocking for long runs.
    """

    def __init__(self):
        # subprocess.Popen instance for ffmpeg, or None
        import threading
        self._proc = None
        self._lock = threading.Lock()

    def is_recording(self) -> bool:
        """Return True if ffmpeg process is running."""
        with self._lock:
            p = self._proc
        return p is not None and p.poll() is None

    def start_recording(
        self,
        output_path: str,
        display: str = ":0.0",
        video_size: str = "3840x2400",
        framerate: int = 60,
        encoder: str = "h264_nvenc",
        bitrate: str = "12M",
        extra_ffmpeg_args: 'list | None' = None,
    ):
        """
        Start ffmpeg recording. Non-blocking.

        - output_path: path to write the .mkv file
        - display: X display for x11grab (e.g. ":0.0")
        - video_size: e.g. "3840x2400"
        - framerate: integer fps
        - encoder: ffmpeg encoder to use ("h264_nvenc", "libx264", etc.)
        - bitrate: target bitrate string for NVENC or other encoders
        - extra_ffmpeg_args: list of additional ffmpeg args (each as separate items)
        """
        import os
        import subprocess

        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                raise RuntimeError("Recording already in progress")

            # Build a safe ffmpeg command; using x11grab and no audio by default
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "x11grab",
                "-video_size", str(video_size),
                "-framerate", str(framerate),
                "-i", str(display),
                "-an",  # no audio
            ]

            # Encoder-specific options
            if encoder == "h264_nvenc":
                cmd += ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr_hq", "-cq", "19", "-b:v", str(bitrate)]
            elif encoder == "h264_vaapi":
                # Example vaapi command fragment; user must ensure vaapi device is present
                cmd += ["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi", "-qp", "24"]
            elif encoder == "libx264":
                cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-b:v", str(bitrate)]
            else:
                # Generic: let user specify encoder and bitrate manually via extra_ffmpeg_args
                cmd += ["-c:v", encoder, "-b:v", str(bitrate)]

            # Container: MKV for resilience
            cmd += [str(output_path)]

            if extra_ffmpeg_args:
                # Insert extra args before output file
                cmd = cmd[:-1] + list(extra_ffmpeg_args) + [cmd[-1]]

            # Start subprocess in a new process group so we can signal the whole group later
            # Provide stdin=PIPE so we can send 'q' for graceful shutdown
            # Redirect stdout/stderr to DEVNULL to prevent pipe-fill blocking on long recordings
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )

    def stop_recording(self, timeout: float = 15.0) -> bool:
        """
        Try to stop ffmpeg cleanly.

        Steps:
          1) If ffmpeg stdin is available, send 'q' (the recommended graceful stop).
          2) Wait up to `timeout` seconds for process to exit.
          3) If still alive, send SIGINT to the process group and wait again.
        Returns True if process exited, False if still running after attempts.
        """
        import os
        import signal

        with self._lock:
            p = self._proc

        if p is None:
            return True

        if p.poll() is not None:
            # already exited
            with self._lock:
                self._proc = None
            return True

        # 1) Try writing 'q' to stdin
        try:
            if p.stdin:
                p.stdin.write(b"q")
                p.stdin.flush()
        except Exception:
            # ignore and fall through to signaling
            pass

        # wait for graceful exit
        try:
            p.wait(timeout=timeout)
            with self._lock:
                self._proc = None
            return True
        except Exception:
            # still alive; try SIGINT to process group (like Ctrl-C)
            try:
                os.killpg(p.pid, signal.SIGINT)
            except Exception:
                pass

            try:
                p.wait(timeout=timeout)
                with self._lock:
                    self._proc = None
                return True
            except Exception:
                return False

    def force_stop(self, wait_timeout: float = 5.0) -> bool:
        """
        Forcefully terminate ffmpeg if it won't stop.

        - First send SIGTERM to the process group.
        - If still alive after wait_timeout, send SIGKILL.
        Returns True if process ended, False otherwise.
        """
        import os
        import signal

        with self._lock:
            p = self._proc

        if p is None:
            return True

        if p.poll() is not None:
            with self._lock:
                self._proc = None
            return True

        try:
            os.killpg(p.pid, signal.SIGTERM)
        except Exception:
            pass

        try:
            p.wait(timeout=wait_timeout)
            with self._lock:
                self._proc = None
            return True
        except Exception:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                p.wait(timeout=2.0)
                with self._lock:
                    self._proc = None
                return True
            except Exception:
                return False

    # Convenience context-manager usage
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # Try graceful stop, then force if necessary
        try:
            self.stop_recording(timeout=5)
        finally:
            self.force_stop()


def main():
    return True

if __name__ == "__main__":
    main()
