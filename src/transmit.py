import socket
import time
import numpy as np
from predict import init_prediction, predict_location
from config import FILTER, K, USE_AGGREGATION

# Initialize prediction
structured_fingerprints = init_prediction()

# Socket configuration
HOST = '10.100.40.206'  # Server hostname or IP address
PORT = 65432            # Port to listen on (non-privileged ports are > 1023)

def get_test_position():
    # Simulate getting a new position
    x, y, z = np.random.rand(), np.random.rand(), 1
    # print(f"Position: ({x:.2f}, {y:.2f}, {z:.2f})")
    return x, y, z
    # return 1, 1, 1

def send_location():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                while True:
                    try:
                        # x, y, floor = predict_location(structured_fingerprints, filter_type=FILTER, k=K, use_aggregation=USE_AGGREGATION)
                        x, y, floor = get_test_position()
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