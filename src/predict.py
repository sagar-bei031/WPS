import math
import sqlite3

from scan_wifi import scan_wifi


def predict_position(networks):
    """Predict position based on current Wi-Fi scan."""
    conn = sqlite3.connect("wifi_data.db")
    cursor = conn.cursor()
    
    # Get all reference fingerprints
    cursor.execute("SELECT position, ssid, bssid, rssi FROM wifi_data")
    reference_data = cursor.fetchall()
    conn.close()

    # Organize reference data by position
    position_data = {}
    for position, ssid, bssid, rssi in reference_data:
        if position not in position_data:
            position_data[position] = {}
        position_data[position][bssid] = rssi

    # Compute similarity (Euclidean Distance)
    min_distance = float('inf')
    predicted_position = None

    for position, reference_rssi in position_data.items():
        distance = 0
        count = 0
        for ssid, bssid, rssi in networks:
            if bssid in reference_rssi:
                distance += (rssi - reference_rssi[bssid]) ** 2
                count += 1
        if count > 0:  # Only consider positions with overlapping networks
            distance = math.sqrt(distance / count)
            if distance < min_distance:
                min_distance = distance
                predicted_position = position

    return predicted_position

if __name__ == "__main__":
    # Scan current Wi-Fi networks
    networks = scan_wifi()

    # Predict position based on current scan
    predicted_position = predict_position(networks)
    if predicted_position:
        print(f"Predicted Position: {predicted_position}")
    else:
        print("No matching position found.")
