import socket
import threading
from concurrent.futures import thread


class TCPServer:
    # socket.gethostbyname(socket.gethostname())
    def __init__(self, host='0.0.0.0', port=9999, command_router=None):
        self.host = host
        self.port = port
        self.command_router = command_router or self.default_router
        self.stop_event = threading.Event()
        self.server_thread = None
        self.conn = None

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
                            conn, addr = s.accept()
                            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
                        except socket.timeout:
                            continue
                finally:
                    print("[✋] TCP Server shutting down...")

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

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

    def stop(self):
        self.stop_event.set()
        if self.server_thread:
            self.server_thread.join()

    def default_router(self, message, conn, addr):
        print(f"[>] Received from {addr}: {message}")
        conn.sendall(b"ACK:DEFAULT_HANDLER\n")

    def handle_start(conn, addr):
        conn.sendall(b"ACK:START_CAPTURE\n")
        # TODO: start aquisition or stream to network via ndi

    def handle_stop(self, conn, addr):
        conn.sendall(b"ACK:STOPPING\n")
        server.stop()

    def handle_status(conn, addr):
        conn.sendall(b"ACK:STATUS:RUNNING\n")


listener = TCPServer()
listener.start()

try:
    threading.Event().wait()
except KeyboardInterrupt:
    print("[!] Received CTRL-C")
    listener.stop()