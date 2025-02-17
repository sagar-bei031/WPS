import sqlite3
from math import sqrt
from scan_wifi import scan_wifi
from config import DB_FILE_PATH

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
    x = sum((1 / d[0]) * d[2] for d in nearest_neighbors if d[0] != 0) / weight_sum
    y = sum((1 / d[0]) * d[3] for d in nearest_neighbors if d[0] != 0) / weight_sum
    floor = nearest_neighbors[0][4]  # Assuming the floor is the same for the nearest neighbors

    return x, y, floor

if __name__ == "__main__":
    print("Scanning Wi-Fi networks for real-time positioning...")
    real_time_data = scan_wifi()
    if real_time_data:
        x, y, floor = find_location(real_time_data)
        print(f"Estimated Location: x={x}, y={y}, floor={floor}")
    else:
        print("No Wi-Fi networks found.")