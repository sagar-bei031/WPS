import sqlite3
from datetime import datetime
from termcolor import colored
from network import get_networks_with_mean_rss
from config import DB_FILE_PATH, SCANS_TO_ADD_SSID

def check_ssid_in_db(bssid):
    """Check if SSID is in the database and return the SSID ID if found."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # Check if SSID exists in the database
    cursor.execute("SELECT id FROM ssids WHERE bssid = ?", (bssid,))
    existing_ssid = cursor.fetchone()
    conn.close()

    if existing_ssid:
        return existing_ssid[0]  # Return existing ssid_id
    else:
        return None

def update_count_for_existing_ssids_in_db(existing_ssids):
    """Update the count for existing SSIDs in the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    for id, count in existing_ssids:
        cursor.execute("""
            UPDATE ssids
            SET appeared_count = appeared_count + ?
            WHERE id = ?
        """, (count, id))

    conn.commit()
    conn.close()

def store_ssids_in_db(ssid, bssid, count):
    """Store Wi-Fi signal data in the database."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # Insert Wi-Fi signal record
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO ssids (ssid, bssid, date, appeared_count)
        VALUES (?, ?, ?, ?)
    """, (ssid, bssid, date, count))

    conn.commit()
    conn.close()

def parse_range(range_str, max_value):
    """Parse a range input like '2', '6', or '9-12' and return a list of integers."""
    numbers = []
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
                raise ValueError(f"Invalid range: {part}")
        elif part.isdigit():
            # Handle single number like '2' or '6'
            num = int(part)
            if 1 <= num <= max_value:
                numbers.append(num - 1)  # Convert to 0-based index
            else:
                raise ValueError(f"Invalid number: {part}")
        else:
            raise ValueError(f"Invalid part: {part}")
    
    if not numbers:
        raise ValueError("Invalid SN or range entered.")

    return numbers

def scan_and_interact():
    """Scan Wi-Fi networks and interactively check/add to the database."""
    # Scan for Wi-Fi networks
    print("Scanning Wi-Fi networks...")
    networks = get_networks_with_mean_rss(scan_count=SCANS_TO_ADD_SSID)
    existing_ssids = []
    new_ssids = []

    if networks:
        network_count = len(networks)
        print(f"\nFound {network_count} {'network' if network_count == 1 else 'networks'}.")
        for network in networks:
            ssid = network.get('ssid')
            bssid = network.get('bssid')
            rss = network.get('rss')
            count = network.get('count', 1)  # Default count to 1 if not provided
            id = check_ssid_in_db(bssid)
            if id:
                existing_ssids.append((id, ssid, bssid, rss, count))
            else:
                new_ssids.append((ssid, bssid, rss, count))
    
    print(f" {len(existing_ssids)} existing and {len(new_ssids)} new.")

    if existing_ssids:
        print("\nExisting ssids:")
        for index, (id, ssid, bssid, rss, count) in enumerate(existing_ssids):
            print(f"{index + 1}. {colored(f'ID: {id}, SSID: {ssid}, BSSID: {bssid}, RSS: {rss}, COUNT: {count}', 'light_green')}")

    if not new_ssids:
        print("\nNo new ssid found to add.")
        if existing_ssids:
            choice = input("Do you want to add more scans to the existing ssids? (y/n): ").strip().lower()
            if choice == 'y':
                update_count_for_existing_ssids_in_db([(id, count) for id, ssid, bssid, rss, count in existing_ssids])
            return

    print("\nNew ssids:")
    for index, (ssid, bssid, rss, count) in enumerate(new_ssids):
        print(f"{index + 1}. {colored(f'SSID: {ssid}, BSSID: {bssid}, RSS: {rss}, COUNT: {count}', 'light_magenta')}")

    try:
        # Ask user to input SN of the new Wi-Fi network to add to the database, or 0 to add all
        choice = input("\nEnter SN of the new Wi-Fi to add to the database (eg. 2, 5-10, 15, 0, all, c<min_count>, s<min_rss>): ").strip()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    if choice:
        sn_range = []
        if choice == '0':
            if existing_ssids:
                update_count_for_existing_ssids_in_db([(id, count) for id, ssid, bssid, rss, count in existing_ssids])
        elif choice.lower() == 'all':
            sn_range = range(len(new_ssids))
        elif choice.startswith('c'):
            try:
                min_count = int(choice[1:])
                sn_range = [i for i, (_, _, _, count) in enumerate(new_ssids) if count >= min_count]
            except ValueError:
                print("Invalid minimum count entered.")
                return
        elif choice.startswith('s'):
            try:
                min_rss = int(choice[1:])
                sn_range = [i for i, (_, _, rss, _) in enumerate(new_ssids) if rss >= min_rss]
            except ValueError:
                print("Invalid minimum RSS entered.")
                return
        else:
            try:
                sn_range = parse_range(choice, len(new_ssids))
            except ValueError as e:
                print(f"Error: {e}")
                return

        count = len(sn_range)
        if sn_range:
            print("\nAdding ssids...")
            for sn in sn_range:
                ssid, bssid, rss, count = new_ssids[sn]
                store_ssids_in_db(ssid, bssid, count)
                print(f"{sn + 1}. {colored(f'SSID: {ssid}, BSSID: {bssid}, COUNT: {count}', 'light_green')}")
        print(f"\n{count} {'ssid' if count == 1 else 'ssids'} added to the database.")
    else:
        print("\nCancelled.")

if __name__ == "__main__":
    scan_and_interact()