import sqlite3
import sys
from datetime import datetime
from pywifi import PyWiFi

def scan_wifi():
    """Scan available Wi-Fi networks and return details."""
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Get the first wireless interface
    iface.scan()
    print("Scanning for networks...")
    scan_results = iface.scan_results()
    networks = []
    for result in scan_results:
        ssid = result.ssid
        bssid = result.bssid
        rssi = result.signal
        networks.append((ssid, bssid, rssi))
    return networks

def store_to_db(position, networks):
    """Store Wi-Fi scan data into an SQLite database."""
    conn = sqlite3.connect("wifi_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_data (
            position TEXT,
            ssid TEXT,
            bssid TEXT,
            rssi INTEGER,
            scan_time TEXT
        )
    """)
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ssid, bssid, rssi in networks:
        cursor.execute(
            "INSERT INTO wifi_data (position, ssid, bssid, rssi, scan_time) VALUES (?, ?, ?, ?, ?)",
            (position, ssid, bssid, rssi, scan_time)
        )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Ensure position is passed as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python scan_store.py <position>")
        sys.exit(1)

    position = sys.argv[1]  # Get the position from command-line arguments

    # Scan for Wi-Fi networks
    networks = scan_wifi()

    # Check if networks were found
    if networks:
        print(f"Found {len(networks)} networks.")
        for ssid, bssid, rssi in networks:
            print(f"SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}")

        # Store networks in the database
        store_to_db(position, networks)
        print("Data stored successfully.")
    else:
        print("No Wi-Fi networks found.")
