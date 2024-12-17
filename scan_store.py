import sqlite3
import sys
from datetime import datetime
from scan_wifi import scan_wifi


def store_to_db(x, y, floor, location, networks):
    """Store Wi-Fi scan data into an SQLite database."""
    conn = sqlite3.connect("wifi_rssi_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_data (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL,
            y REAL,
            floor INTEGER,
            location TEXT,
            ssid TEXT,
            bssid TEXT,
            rssi INTEGER,
            scan_time DATETIME
        )
    """)
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ssid, bssid, rssi in networks:
        cursor.execute(
            "INSERT INTO wifi_data (x, y, floor, location, ssid, bssid, rssi, scan_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (x, y, floor, location, ssid, bssid, rssi, scan_time)
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Ensure position is passed as command-line arguments
    if len(sys.argv) != 5:
        print("Usage: python scan_store.py <x> <y> <floor> <location>")
        sys.exit(1)

    try:
        x = float(sys.argv[1])  # X-coordinate
        y = float(sys.argv[2])  # Y-coordinate
        floor = int(sys.argv[3])  # Floor
        location = sys.argv[4]  # Location
    except ValueError:
        print("Error: x, y, and floor must be numeric values. Floor must be an integer.")
        sys.exit(1)

    # Scan for Wi-Fi networks
    networks = scan_wifi()

    # Check if networks were found
    if networks:
        print(f"Found {len(networks)} networks.")
        for ssid, bssid, rssi in networks:
            print(f"SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}")

        # Store networks in the database
        store_to_db(x, y, floor, location, networks)
        print("Data stored successfully.")
    else:
        print("No Wi-Fi networks found.")
