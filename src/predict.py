import sqlite3
import csv
# import numpy as np
import time
from math import sqrt
from network import get_networks, get_networks_with_mean_rss, get_networks_with_median_rss
from config import DB_FILE_PATH, USE_FILTERED_RSS, PREDICTION_FILTER_TYPE, FilterType

def get_fingerprints_from_db(use_filtered):
    """Retrieve all Wi-Fi fingerprints from the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    
    if use_filtered:
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
    structured_data = []
    for key, rss_values in data.items():
        location_id, x, y, floor = key
        row = {"location_id": location_id, "x": x, "y": y, "floor": floor}
        row.update(rss_values)
        structured_data.append(row)

    return structured_data

def save_structured_data_to_file(structured_data, filename="structured_data.csv"):
    """Save the structured data to a CSV file."""
    if not structured_data:
        return

    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=structured_data[0].keys())
        writer.writeheader()
        writer.writerows(structured_data)

def calculate_distance(rssi1, rssi2):
    """Calculate the Euclidean distance between two RSSI values using NumPy."""
    # return np.sqrt(np.sum((np.array(rssi1) - np.array(rssi2)) ** 2))
    return sqrt(sum((r1 - r2) ** 2 for r1, r2 in zip(rssi1, rssi2)))

def find_location(structured_data, real_time_networks, k=3, use_filtered=False):
    """Find the location using the W_KNN algorithm."""
    distances = []
    for fingerprint in structured_data:
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
        return None, None, None  # Handle the case where no neighbors are found

    # Calculate the weighted average of the nearest neighbors
    weight_sum = sum(1 / d[0] for d in nearest_neighbors if d[0] != 0)
    if weight_sum == 0:
        return None, None, None  # Handle the case where weight_sum is zero

    x = sum((1 / d[0]) * d[2] for d in nearest_neighbors if d[0] != 0) / weight_sum
    y = sum((1 / d[0]) * d[3] for d in nearest_neighbors if d[0] != 0) / weight_sum
    floor = nearest_neighbors[0][4]  # Assuming the floor is the same for the nearest neighbors

    return x, y, floor

if __name__ == "__main__":
    fingerprints = get_fingerprints_from_db(use_filtered=USE_FILTERED_RSS)
    structured_data = structure_data(fingerprints)
    save_structured_data_to_file(structured_data)  # Save the structured data to a file

    while True:
        try:
            if  PREDICTION_FILTER_TYPE is FilterType.NONE:
                    real_time_networks = get_networks()
            elif PREDICTION_FILTER_TYPE is FilterType.MEAN:
                real_time_networks = get_networks_with_mean_rss(scan_count=10, sleep_time=0)
            elif PREDICTION_FILTER_TYPE is FilterType.MEDIAN:
                    real_time_networks = get_networks_with_median_rss(scan_count=10, sleep_time=0)
            else:
                    raise ValueError("Invalid prediction filter type.")
                            
            x, y, floor = find_location(structured_data, real_time_networks, k=3, use_filtered=USE_FILTERED_RSS)
            if x is not None and y is not None:
                print(f"{time.time()}: Predicted location: x={x:.2f}, y={y:.2f}, floor={floor}")
            else:
                print("No location found.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            break