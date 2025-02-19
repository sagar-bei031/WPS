import sqlite3
from time import sleep
from datetime import datetime
from termcolor import colored

from network import get_networks
from config import DB_FILE_PATH, SCANS_FOR_FINGERPRINT, RSS_FOR_UNREACHABLE, DELAY_BETWEEN_SCANS

def store_scan_pass_to_db(location_id, scan_pass, pass_time):
    """Store multiple passes of scan data of WiFi signals into the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # Insert scan pass record
    cursor.execute("""
        INSERT INTO scan_passes (location_id, pass_time)
        VALUES (?, ?)
    """, (location_id, pass_time))
    pass_id = cursor.lastrowid

    # Get all SSIDs from the database
    cursor.execute("SELECT id, ssid, bssid FROM ssids")
    all_ssids = cursor.fetchall()

    for networks, scan_time in scan_pass:
        # Insert scan record
        cursor.execute("""
            INSERT INTO scans (pass_id, scan_time)
            VALUES (?, ?)
        """, (pass_id, scan_time))
        scan_id = cursor.lastrowid

        detected_ssids = set()

        for ssid, bssid, rss in networks:
            # Check if SSID already exists in the database
            cursor.execute("SELECT id FROM ssids WHERE ssid = ? AND bssid = ?", (ssid, bssid))
            existing_ssid = cursor.fetchone()

            if existing_ssid:
                ssid_id = existing_ssid[0]  # Use existing SSID ID
                detected_ssids.add(ssid_id)
                print(colored(f'ID: {ssid_id}, SSID: {ssid}, BSSID: {bssid}, RSSI: {rss}', "light_green"))
            else:
                print(colored(f'SSID: {ssid}, BSSID: {bssid}, RSSI: {rss}', "light_yellow"))
                continue  # Skip the scan for SSID if it's not in the database

            # Insert Wi-Fi signal record
            cursor.execute("""
                INSERT INTO wifi_signals (scan_id, ssid_id, rss)
                VALUES (?, ?, ?)
            """, (scan_id, ssid_id, rss))

        # Assign RSS_FOR_UNREACHABLE to SSIDs not detected in this scan
        for ssid_id, ssid, bssid in all_ssids:
            if ssid_id not in detected_ssids:
                cursor.execute("""
                    INSERT INTO wifi_signals (scan_id, ssid_id, rss)
                    VALUES (?, ?, ?)
                """, (scan_id, ssid_id, RSS_FOR_UNREACHABLE))

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
    cursor = conn.cursor()
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
            print("\nCancelled.")
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

        location = get_location_from_db(location_id)
        if location is None:
            print(f"\nNo location found with id={location_id}")
            continue
        else:
            location_id, x, y, floor, location_name = location[0], location[1], location[2], location[3], location[4]
            print(f"location_id: {location_id}, x: {x}, y: {y}, floor: {floor}, location_name: {location_name}")
            break

    scan_pass = []
    pass_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{colored('Do not Move! Fingerprinting...', 'yellow')}")

    try:
        for i in range(SCANS_FOR_FINGERPRINT):
            # Scan for Wi-Fi networks
            scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            networks = get_networks()
            if networks:
                scan_pass.append((networks, scan_time))

            # Display loading bar
            progress = (i + 1) / SCANS_FOR_FINGERPRINT * 100
            bar_length = 40
            block = int(bar_length * progress / 100)
            hash_color = "green" if networks else "red"
            text = f"\rScanning: [{colored('#', hash_color) * block + '-' * (bar_length - block)}] {i + 1}/{SCANS_FOR_FINGERPRINT}"
            print(text, end='', flush=True)
            sleep(DELAY_BETWEEN_SCANS)

    except KeyboardInterrupt:
        print("\nCancelled.")
        exit()

    if scan_pass:
        store_scan_pass_to_db(location_id, scan_pass, pass_time)
        print(f"\n{colored('Fingerprinting completed successfully!', 'green')}")
    else:
        print("No Wi-Fi networks found. Please try again.")
        exit()