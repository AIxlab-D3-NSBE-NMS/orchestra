import socket
import threading

class TCPServer:
    def __init__(self, host='0.0.0.0', port=9999, command_router=None):
        self.host = host
        self.port = port
        self.command_router = command_router or self.default_router
        self.stop_event = threading.Event()
        self.server_thread = None

    def default_router(self, message, conn, addr):
        print(f"[>] Received from {addr}: {message}")
        conn.sendall(b"ACK:DEFAULT_HANDLER\n")

    def start(self):
        def run():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, self.port))
                s.listen()
                print(f"[🔌] TCP Server listening on {self.host}:{self.port}")
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

    def handle_client(self, conn, addr):
        with conn:
            try:
                data = conn.recv(1024).decode().strip()
                if data:
                    self.command_router(data, conn, addr)
            except Exception as e:
                print(f"[!] Error handling client {addr}: {e}")

    def stop(self):
        self.stop_event.set()
        if self.server_thread:
            self.server_thread.join()
