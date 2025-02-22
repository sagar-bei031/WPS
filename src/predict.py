import sqlite3
import numpy as np
import csv
import time
from math import sqrt
from network import get_networks
from config import DB_FILE_PATH, FILTER, FilterType, MOVING_AVERAGE_WINDOW, EXP_FILTER_ALPHA, USE_AGGREGATION, K, STRUCTURED_FINGERPRINTS_FILE

def get_fingerprints_from_db(use_aggregation=True):
    """Retrieve all Wi-Fi fingerprints from the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    
    if use_aggregation:
        cursor.execute("""
            SELECT l.id, l.x, l.y, l.floor, s.bssid, f.agg_rss
            FROM filtered_wifi_signals f
            JOIN locations l ON f.location_id = l.id
            JOIN ssids s ON f.ssid_id = s.id
        """)
    else:
        cursor.execute("""
            SELECT l.id, l.x, l.y, l.floor, s.bssid, w.rss
            FROM wifi_signals w
            JOIN wifi_scans sc ON w.scan_id = sc.id
            JOIN scan_sessions ss ON sc.session_id = ss.id
            JOIN locations l ON ss.location_id = l.id
            JOIN ssids s ON w.ssid_id = s.id
        """)
    
    fingerprints = cursor.fetchall()
    conn.close()
    return fingerprints

def structure_data(fingerprints):
    """Structure the data into a list of dictionaries format."""
    data = {}
    for location_id, x, y, floor, bssid, rss in fingerprints:
        key = (location_id, x, y, floor)
        if key not in data:
            data[key] = {}
        data[key][bssid] = rss

    # Convert the dictionary to a list of dictionaries
    structured_fingerprints = []
    for key, rss_values in data.items():
        location_id, x, y, floor = key
        row = {"location_id": location_id, "x": x, "y": y, "floor": floor}
        row.update(rss_values)
        structured_fingerprints.append(row)

    return structured_fingerprints

def save_structured_fingerprints_to_file(structured_fingerprints, filename=STRUCTURED_FINGERPRINTS_FILE):
    """Save the structured data to a CSV file."""
    if not structured_fingerprints:
        return

    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=structured_fingerprints[0].keys())
        writer.writeheader()
        writer.writerows(structured_fingerprints)

def calculate_distance(rssi1, rssi2):
    """Calculate the Euclidean distance between two RSSI values."""
    return np.sqrt(np.sum((np.array(rssi1) - np.array(rssi2)) ** 2))

def find_location(structured_fingerprints, real_time_networks, k=K, use_aggregation=True):
    """Find the location using the W_KNN algorithm."""
    distances = []
    for fingerprint in structured_fingerprints:
        location_id = fingerprint["location_id"]
        x = fingerprint["x"]
        y = fingerprint["y"]
        floor = fingerprint["floor"]
        rss_values = [fingerprint.get(rt_network["bssid"], -100) for rt_network in real_time_networks]

        rt_rss_values = [rt_network["rss"] for rt_network in real_time_networks]
        distance = calculate_distance(rss_values, rt_rss_values)
        distances.append((distance, location_id, x, y, floor))

    # Sort by distance and get the k-nearest neighbors
    distances.sort(key=lambda x: x[0])
    nearest_neighbors = distances[:k]

    if not nearest_neighbors:
        return None, None, None

    # Calculate the weighted average of the nearest neighbors
    weight_sum = np.sum([1 / d[0] for d in nearest_neighbors if d[0] != 0])
    if weight_sum == 0:
        return None, None, None  # Handle the case where weight_sum is zero

    x = np.sum([(1 / d[0]) * d[2] for d in nearest_neighbors if d[0] != 0]) / weight_sum
    y = np.sum([(1 / d[0]) * d[3] for d in nearest_neighbors if d[0] != 0]) / weight_sum
    floor = nearest_neighbors[0][4]  # Assuming the floor is the same for the nearest neighbors

    return x, y, floor

def moving_average_filter(data, window_size):
    """Apply a moving average filter to the data."""
    filtered_data = []
    for i in range(len(data)):
        if i < window_size:
            filtered_data.append(data[i])
        else:
            window = data[i - window_size:i]
            avg = sum(window) / window_size
            filtered_data.append(avg)
    return filtered_data

def exponential_filter(data, alpha):
    """Apply an exponential filter to the data."""
    filtered_data = [data[0]]  # Initialize with the first value
    for i in range(1, len(data)):
        filtered_value = alpha * data[i] + (1 - alpha) * filtered_data[-1]
        filtered_data.append(filtered_value)
    return filtered_data

def filter_real_time_networks(real_time_networks, filter_type):
    """Filter the real-time networks based on the specified filter type."""
    if filter_type == FilterType.NONE:
        return real_time_networks
    elif filter_type == FilterType.MOVING_AVERAGE:
        for network in real_time_networks:
            network["rss"] = moving_average_filter([network["rss"]], MOVING_AVERAGE_WINDOW)[-1]
        return real_time_networks
    elif filter_type == FilterType.EXPONENTIAL:
        for network in real_time_networks:
            network["rss"] = exponential_filter([network["rss"]], EXP_FILTER_ALPHA)[-1]
        return real_time_networks
    else:
        raise ValueError("Invalid prediction filter type.")

def predict_location(structured_fingerprints, filter_type, k=3, use_aggregation=False):
    """Predict the location based on real-time networks."""
    real_time_networks = filter_real_time_networks(get_networks(), filter_type)
    x, y, floor = find_location(structured_fingerprints, real_time_networks, k, use_aggregation)
    return x, y, floor

def init_prediction():
    """Initialize the prediction process."""
    fingerprints = get_fingerprints_from_db(use_aggregation=USE_AGGREGATION)
    structured_fingerprints = structure_data(fingerprints)
    return structured_fingerprints

if __name__ == "__main__":
    structured_fingerprints = init_prediction()
    save_structured_fingerprints_to_file(structured_fingerprints)  # Save the structured data to a file

    while True:
        try:
            x, y, floor = predict_location(structured_fingerprints, filter_type=FILTER, k=K, use_aggregation=USE_AGGREGATION)
            if x is not None and y is not None:
                now = time.strftime("%H:%M:%S")
                print(f"{now}: Predicted location: x={x:.2f}, y={y:.2f}, floor={floor}")
            else:
                print("No location found.")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nCancelled.")
            break