import socket
import time

# Socket configuration
HOST = 'localhost'  # Server hostname or IP address
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

def receive_location():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, PORT))
                s.listen()
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        try:
                            data = conn.recv(1024)
                            if not data:
                                break
                            location_data = data.decode('utf-8')
                            print(f"Received: {location_data}")
                            x, y, floor = map(float, location_data.split(','))
                            yield x, y, floor
                        except ConnectionResetError:
                            print("Connection lost. Waiting for reconnection...")
                            break
        except OSError:
            print("Address already in use. Retrying in 1 second...")
            time.sleep(1)

def get_location():
    location_generator = receive_location()
    while True:
        try:
            x, y, floor = next(location_generator)
        except StopIteration:
            break

if __name__ == "__main__":
    get_location()