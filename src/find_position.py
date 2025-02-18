import sqlite3
from math import sqrt
from scan_wifi import scan_wifi
from config import DB_FILE_PATH
from time import sleep

def get_fingerprints_from_db():
    """Retrieve all Wi-Fi fingerprints from the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id, l.x, l.y, l.floor, s.ssid, s.bssid, w.rssi
        FROM wifi_signals w
        JOIN scans sc ON w.scan_id = sc.id
        JOIN locations l ON sc.location_id = l.id
        JOIN ssids s ON w.ssid_id = s.id 
    """)
    fingerprints = cursor.fetchall()
    conn.close()
    return fingerprints

def calculate_distance(rssi1, rssi2):
    """Calculate the Euclidean distance between two RSSI values."""
    return sqrt((rssi1 - rssi2) ** 2)

def find_location(real_time_data, k=3):
    """Find the location using the W_KNN algorithm."""
    fingerprints = get_fingerprints_from_db()
    distances = []

    for location_id, x, y, floor, ssid, bssid, rssi in fingerprints:
        for rt_ssid, rt_bssid, rt_rssi, _ in real_time_data:
            if ssid == rt_ssid and bssid == rt_bssid:
                distance = calculate_distance(rssi, rt_rssi)
                distances.append((distance, location_id, x, y, floor))

    # Sort by distance and get the k-nearest neighbors
    distances.sort(key=lambda x: x[0])
    nearest_neighbors = distances[:k]

    # Calculate the weighted average of the nearest neighbors
    weight_sum = sum(1 / d[0] for d in nearest_neighbors if d[0] != 0)
    if weight_sum == 0:
        return None, None, None  # Handle the case where weight_sum is zero

    x = sum((1 / d[0]) * d[2] for d in nearest_neighbors if d[0] != 0) / weight_sum
    y = sum((1 / d[0]) * d[3] for d in nearest_neighbors if d[0] != 0) / weight_sum
    floor = nearest_neighbors[0][4]  # Assuming the floor is the same for the nearest neighbors

    return x, y, floor

def average_location(locations):
    """Calculate the average location from a list of locations."""
    if not locations:
        return None, None, None

    x_sum = sum(loc[0] for loc in locations)
    y_sum = sum(loc[1] for loc in locations)
    floor_sum = sum(loc[2] for loc in locations)

    return x_sum / len(locations), y_sum / len(locations), floor_sum / len(locations)

if __name__ == "__main__":
    print("Finding the location using the W-KNN algorithm...")
    try:
        while True:
            try:
                real_time_data = scan_wifi(scan_count=10)
            except Exception as e:
                print(f"Error scanning Wi-Fi networks: {e}")
                continue

            if real_time_data:
                locations = []
                for _ in range(5):  # Average over 5 scans
                    x, y, floor = find_location(real_time_data)
                    if x is not None and y is not None and floor is not None:
                        locations.append((x, y, floor))
                    sleep(0.1)  # Sleep for 100ms between scans

                avg_x, avg_y, avg_floor = average_location(locations)
                if avg_x is not None and avg_y is not None and avg_floor is not None:
                    print(f"Estimated Location: x={avg_x:.2f}, y={avg_y:.2f}, floor={avg_floor}")
                else:
                    print("Could not determine location. No matching Wi-Fi signals found.")
            else:
                print("No Wi-Fi networks found.")

            sleep(0.5)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")