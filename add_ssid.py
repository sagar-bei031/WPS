import sqlite3
from datetime import datetime
from termcolor import colored
from scan_wifi import scan_wifi


def check_and_add_ssid_to_db(ssid, bssid):
    """Check if SSID is in the database, and add if not."""
    conn = sqlite3.connect("wifi_fingerprints.db")
    cursor = conn.cursor()

    # Check if SSID exists in the database
    cursor.execute("SELECT id FROM ssids WHERE ssid = ? AND bssid = ?", (ssid, bssid))
    existing_ssid = cursor.fetchone()

    if existing_ssid:
        conn.close()
        return existing_ssid[0]  # Return existing ssid_id
    else:
        conn.close()
        return None


def parse_range(range_str, max_value):
    """Parse a range input like '2', '6', or '9-12' and return a list of integers."""
    print(f"Parsing range: {range_str}")  # Debug print to check the input
    numbers = []
    try:
        # Split the input string by commas
        parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Handle range like '9-12'
                start, end = part.split('-')
                start, end = int(start), int(end)
                if start <= end and 1 <= start <= max_value and 1 <= end <= max_value:
                    numbers.extend(range(start - 1, end))  # Convert to 0-based index
                else:
                    print(f"Invalid range: {part}")
            elif part.isdigit():
                # Handle single number like '2' or '6'
                num = int(part)
                if 1 <= num <= max_value:
                    numbers.append(num - 1)  # Convert to 0-based index
                else:
                    print(f"Invalid number: {part}")
            else:
                print(f"Invalid part: {part}")
    except ValueError:
        pass
    
    if not numbers:
        print("Invalid SN or range entered.")

    print(numbers)
    return numbers



def scan_and_interact():
    """Scan Wi-Fi networks and interactively check/add to the database."""
    # Scan for Wi-Fi networks
    networks = scan_wifi()

    if networks:
        count = len(networks)
        print(f"\nFound {count} {'network' if count == 1 else 'networks'}.")
        existing_ssids = []
        new_ssids = []
        for network in networks:
            ssid, bssid = network[:2]
            # Display SSID in green if it exists in the database, yellow if not
            if check_and_add_ssid_to_db(ssid, bssid):
                existing_ssids.append(network)
            else:
                new_ssids.append(network)
    
    print(f" {len(existing_ssids)} existing and {len(new_ssids)} new.")

    if existing_ssids:
        print("\nExisting ssids:")
        for index, (ssid, bssid, rssi) in enumerate(existing_ssids):
            print(f"{index + 1}. {colored(f'SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}', "light_green")}")

    if not new_ssids:
        print("\nNo new ssid found to add.")
        return

    print("\nNew ssids:")
    for index, (ssid, bssid, rssi) in enumerate(new_ssids):
        print(f"{index + 1}. {colored(f'SSID: {ssid}, BSSID: {bssid}, RSSI: {rssi}', "light_magenta")}")

    try:
        # Ask user to input SN of the new Wi-Fi network to add to the database, or 0 to add nothing
        choice = input("\nEnter SN of the new Wi-Fi to add to the database (eg. 2, 5-10, 15): ").strip()
    except KeyboardInterrupt:
        print("\n0 ssid added to the database. Exiting...")
        return
    
    if choice:
        sn_range = parse_range(choice, len(new_ssids))
        count = len(sn_range)
        if sn_range:
            print("\nAdded ssid:")
            for sn in sn_range:
                ssid, bssid = new_ssids[sn][:2]
                store_ssids_in_db(ssid, bssid)
                print(f"{sn + 1}. {colored(f'SSID: {ssid}, BSSID: {bssid}', "light_green")}")
            print(f"\n{count} {'ssid' if count == 1 else 'ssids'} added to the database.")
    else:
        print("\n0 ssid added to the database.")
        


def store_ssids_in_db(ssid, bssid):
    """Store Wi-Fi signal data in the database."""
    conn = sqlite3.connect("wifi_fingerprints.db")
    cursor = conn.cursor()

    # Insert Wi-Fi signal record
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO ssids (ssid, bssid, date)
        VALUES (?, ?, ?)
    """, (ssid, bssid, date))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    scan_and_interact()
