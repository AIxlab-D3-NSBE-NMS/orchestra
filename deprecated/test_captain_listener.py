# captain_tcp_listener.py
import socket
import threading

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 9999       # Port to listen on

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    with conn:
        data = conn.recv(1024).decode().strip()
        print(f"[>] Received: {data}")
        if data == "START_CAPTURE":
            print("[✓] Trigger received: START_CAPTURE")zz
            conn.sendall(b"ACK:START_CAPTURE\n")
        else:
            print("[!] Unknown command")
            conn.sendall(b"NACK:UNKNOWN_COMMAND\n")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            

if __name__ == "__main__":
    start_server()
