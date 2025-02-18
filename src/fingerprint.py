import sqlite3
from datetime import datetime
from termcolor import colored

from model import initialize_database
from scan_wifi import scan_wifi
from config import DB_FILE_PATH, TOTAL_SCANS_FOR_FINGERPRINT


def store_scan_to_db(location_id, networks):
    """Store Wi-Fi scan data into the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # Insert scan record
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO scans (location_id, scan_time)
        VALUES (?, ?)
    """, (location_id, scan_time))
    scan_id = cursor.lastrowid

    # Insert or retrieve SSID IDs and Wi-Fi signals
    for ssid, bssid, rssi, _ in networks:
        # Check if SSID already exists in the database
        cursor.execute("SELECT id FROM ssids WHERE ssid = ? AND bssid = ?", (ssid, bssid))
        existing_ssid = cursor.fetchone()

        if existing_ssid:
            ssid_id = existing_ssid[0]  # Use existing SSID ID
            print(f"{colored(f'ID: {ssid_id}, SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}', "light_green")}")
        else:
            print(f"{colored(f'SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}', "light_yellow")}")
            continue  # Skip the scan for SSID if it's not in the database

        # Insert Wi-Fi signal record
        cursor.execute("""
            INSERT INTO wifi_signals (scan_id, ssid_id, rssi)
            VALUES (?, ?, ?)
        """, (scan_id, ssid_id, rssi))

    conn.commit()
    conn.close()


def get_location_from_db(location_id):
    """Check if location ID exists in the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
    location = cursor.fetchone()
    conn.close()
    return location


def get_all_locations_from_db():
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations")
    locations = cursor.fetchall()
    conn.close()
    return locations

def get_ssid_id_from_db(ssid, bssid):
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor
    cursor.execute("SELECT id FROM ssids WHERE ssid = ? AND bssid = ?", (ssid, bssid))
    selected_ssid = cursor.fetchone()
    conn.close()
    if selected_ssid:
        return selected_ssid[0]
    else:
        return None
    

if __name__ == "__main__":
    while True:
        try:
            location_id = input("\nEnter location ID or 0 to see locations: ").strip()

        except KeyboardInterrupt:
            print("\nExiting program.")
            exit()

        if location_id == "0":
            locations = get_all_locations_from_db()
            if locations:
                print("\nExisting Locations:")
                print("ID | X | Y | Floor | Location Name")
                for loc in locations:
                    print(f"{loc[0]} | {loc[1]} | {loc[2]} | {loc[3]} | {loc[4]}")
            else:
                print("\nNo locations found.")
            location_id = input("\nEnter location ID: ").strip()
        else:
            try:
                location_id = int(location_id)
            except ValueError:
                print("Error: Invalid input. Please enter a numeric value.")
                continue

        location =  get_location_from_db(location_id)
        if location is None:
            print(f"\nNo location found with id={location_id}")
            continue
        else:
            location_id, x, y, floor, location_name = location[0], location[1], location[2], location[3], location[4]
            print(f"loaction_id: {location_id}, x: {x}, y: {y}, floor: {floor}, location_name: {location_name}")
            break

    # Scan for Wi-Fi networks
    print(f"\n{colored("Do not Move!", "yellow")}")
    networks = scan_wifi(TOTAL_SCANS_FOR_FINGERPRINT)

    if networks:
        print(f"Found {len(networks)} networks:")
        store_scan_to_db(location_id, networks)
    else: 
        print("No networks found.")
