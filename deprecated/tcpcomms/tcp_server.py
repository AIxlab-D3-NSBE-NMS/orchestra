import socket
import threading
from concurrent.futures import thread
import cv2
# todo: use inputParser?

class TCPServer:
    # socket.gethostbyname(socket.gethostname())
    def __init__(self, host='0.0.0.0', port=9999, command_router=None):
        self.status = 'STANDBY'
        self.host = host
        self.port = port
        self.command_router = command_router or self.default_router
        self.stop_event = threading.Event()
        self.server_thread = None
        self.conn = None
        self.handler = None

        self.command_map = {
            "START_CAPTURE": self.handle_start,
            "STOP_SERVER": self.handle_stop,
            "STATUS": self.handle_status,
            "SHOW_CAM_FEED_LOCAL": self.handle_local_stream,
        }

        self.webcam = cv2.VideoCapture(0)


    def start(self):
        def run():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, self.port))
                s.listen()
                s.settimeout(1.0)  # Check for stop_event every second
                print(f"[🔌] TCP Server listening on {self.host}:{self.port}")
                try:
                    while not self.stop_event.is_set():
                        try:
                            self.conn, addr = s.accept()
                            threading.Thread(target=self.handle_client, args=(self.conn, addr), daemon=True).start()
                        except socket.timeout:
                            continue
                finally:
                    print("[✋] TCP Server shutting down...")

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self.status = 'RUNNING'
    def stop(self):
        self.stop_event.set()
        if self.server_thread:
            self.server_thread.join()
        self.status = 'STOPPED'
    def handle_client(self, conn, addr): # parses messages to the command_router
        print(f"[+] Connection from {addr}")
        with conn:
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break  # Client closed connection
                    message = data.decode().strip()
                    self.command_router(message, conn, addr)
            except Exception as e:
                print(f"[!] Error handling client {addr}: {e}")
    def default_router(self, message, conn, addr):
        self.handler = self.command_map.get(message)
        if self.handler:
            self.handler(conn, addr)
            self.handler = None # should we restart it?
        else:
            conn.sendall(b"NACK:UNKNOWN_COMMAND\n")
        print(f"[>] Received from {addr}: {message}")
        conn.sendall(b"ACK:DEFAULT_HANDLER\n")
    def handle_start(self, conn, addr):
        conn.sendall(b"ACK:START_CAPTURE\n")
        # TODO: start acquisition or stream to network via ndi
    def handle_stop(self, conn, addr):
        conn.sendall(b"ACK:STOPPING\n")
        self.stop()
    def handle_status(self, conn, addr):
        conn.sendall(b"ACK:STATUS:RUNNING\n")
    def get_status(self, conn, addr):
        print(self.status)
        return self.status
    def handle_local_stream(self, conn, addr):
        cv2.namedWindow("preview")
        if self.webcam.isOpened():
            rval, frame = self.webcam.read()
        else:
            rval = False

        while rval:
            cv2.imshow("preview", frame)
            rval, frame = self.webcam.read()
            key = cv2.waitKey(20)
            if key == 27:
                break
        cv2.destroyWindow("preview")
        self.webcam.release()

listener = TCPServer()
listener.start()

try:
    threading.Event().wait()
except KeyboardInterrupt:
    print("[!] Received CTRL-C")
    try:
        listener.stop()
    finally:
        print('process already stopped')
    listener.stop()