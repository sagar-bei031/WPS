import sqlite3
import subprocess
import json

# Database setup
def setup_database():
    conn = sqlite3.connect("wifi_positioning.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT NOT NULL,
            ssid TEXT,
            bssid TEXT,
            rssi INTEGER
        )
    """)
    conn.commit()
    return conn, cursor

# Function to scan Wi-Fi
def scan_wifi():
    try:
        # Execute Linux Wi-Fi scan command
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID,BSSID,SIGNAL', 'dev', 'wifi'],
                                stdout=subprocess.PIPE,
                                text=True)
        output = result.stdout.strip()
        networks = []
        for line in output.splitlines():
            parts = line.split(':')
            if len(parts) == 3:
                ssid, bssid, rssi = parts
                networks.append({"ssid": ssid, "bssid": bssid, "rssi": int(rssi)})
        return networks
    except Exception as e:
        print(f"Error scanning Wi-Fi: {e}")
        return []

# Save scan data to database
def save_to_database(cursor, conn, position, wifi_data):
    for network in wifi_data:
        cursor.execute("""
            INSERT INTO wifi_scans (position, ssid, bssid, rssi)
            VALUES (?, ?, ?, ?)
        """, (position, network['ssid'], network['bssid'], network['rssi']))
    conn.commit()
    print("Data saved successfully!")

# Main script
if __name__ == "__main__":
    position = input("Enter current position (e.g., 'Room A, Corner 1'): ")
    
    # Setup database
    conn, cursor = setup_database()

    # Scan Wi-Fi
    wifi_data = scan_wifi()
    if wifi_data:
        print("Wi-Fi scan completed. Saving data to database...")
        save_to_database(cursor, conn, position, wifi_data)
    else:
        print("No Wi-Fi networks found.")

    # Close database connection
    conn.close()
    print("Database connection closed.")
