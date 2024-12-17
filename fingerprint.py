import sqlite3
from datetime import datetime

from model import initialize_database
from scan_wifi import scan_wifi


def store_scan_to_db(location_id, networks):
    """Store Wi-Fi scan data into the database."""
    conn = sqlite3.connect("wifi_fingerprints.db")
    cursor = conn.cursor()

    # Insert scan record
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO scans (location_id, scan_time)
        VALUES (?, ?)
    """, (location_id, scan_time))
    scan_id = cursor.lastrowid

    # Insert or retrieve SSID IDs and Wi-Fi signals
    for ssid, bssid, rssi in networks:
        # Check if SSID already exists in the database
        cursor.execute("SELECT id FROM ssids WHERE ssid = ? AND bssid = ?", (ssid, bssid))
        existing_ssid = cursor.fetchone()

        if existing_ssid:
            ssid_id = existing_ssid[0]  # Use existing SSID ID
        else:
            print(f"SSID '{ssid}' not found in database. Skipping scan for this SSID.")
            continue  # Skip the scan for SSID if it's not in the database

        # Insert Wi-Fi signal record
        cursor.execute("""
            INSERT INTO wifi_signals (scan_id, ssid_id, bssid, rssi)
            VALUES (?, ?, ?, ?)
        """, (scan_id, ssid_id, bssid, rssi))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    while True:
        # Ask user for location information or to view existing locations
        print("Do you want to view existing locations? (Y/n): ", end="")
        choice = input().strip().lower()

        if choice == "y":
            # Display existing locations
            conn = sqlite3.connect("wifi_fingerprints.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM locations")
            locations = cursor.fetchall()
            conn.close()

            if locations:
                print("\nExisting Locations:")
                print("ID | X | Y | Floor | Location Name")
                for loc in locations:
                    print(f"{loc[0]} | {loc[1]} | {loc[2]} | {loc[3]} | {loc[4]}")
            else:
                print("\nNo locations found.")

        # Ask for location details
        print("\nEnter location details.")
        try:
            x = float(input("X-coordinate: "))
            y = float(input("Y-coordinate: "))
            floor = int(input("Floor: "))
            location_name = input("Location name: ").strip()
        except ValueError:
            print("Error: Invalid input. Please enter numeric values for X, Y, and floor.")
            continue

        # Confirm scanning
        print("Proceed with scanning Wi-Fi networks at this location? (Y/n): ", end="")
        choice = input().strip().lower()
        if choice != "y":
            print("Skipping scan...")
            continue

        # Scan for Wi-Fi networks
        networks = scan_wifi()

        if networks:
            print(f"\nFound {len(networks)} networks:")
            for ssid, bssid, rssi in networks:
                print(f"SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}")

            # Confirm storing data
            print("\nDo you want to store this data in the database? (Y/n): ", end="")
            choice = input().strip().lower()
            if choice == "y":
                store_scan_to_db(x, y, floor, location_name, networks)
                print("Data stored successfully.")
            else:
                print("Data not stored.")
        else:
            print("No Wi-Fi networks found.")

        # Ask to continue or exit
        print("\nDo you want to perform another scan? (Y/n): ", end="")
        choice = input().strip().lower()
        if choice != "y":
            print("Exiting program.")
            break
