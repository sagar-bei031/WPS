import socket
import time
from predict import init_prediction, predict_location
from config import FILTER, K, USE_AGGREGATION

# Initialize prediction
structured_fingerprints = init_prediction()

# Socket configuration
HOST = 'localhost'  # Server hostname or IP address
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

def send_location():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                while True:
                    try:
                        x, y, floor = predict_location(structured_fingerprints, filter_type=FILTER, k=K, use_aggregation=USE_AGGREGATION)
                        if x is not None and y is not None:
                            location_data = f"{x:.2f},{y:.2f},{floor}"
                            s.sendall(location_data.encode('utf-8'))
                            print(f"Sent: {location_data}")
                        else:
                            print("No location found.")
                        time.sleep(0.1)
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        print("Connection lost. Reconnecting...")
                        break
        except ConnectionRefusedError:
            print("Receiver not found. Retrying in 1 second...")
            time.sleep(1)

if __name__ == "__main__":
    send_location()