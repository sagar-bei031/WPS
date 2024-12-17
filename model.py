import sqlite3

def initialize_database():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect("wifi_fingerprints.db")
    cursor = conn.cursor()

    # Create the `locations` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL,
            y REAL,
            floor INTEGER,
            location_name TEXT UNIQUE
        )
    """)

    # Create the `ssids` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ssid TEXT,
            bssid TEXT UNIQUE,
            date DATETIME
        )
    """)

    # Create the `scans` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            scan_time DATETIME,
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
    """)

    # Create the `wifi_signals` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            ssid_id INTEGER,
            rssi INTEGER,
            FOREIGN KEY (scan_id) REFERENCES scans (id),
            FOREIGN KEY (ssid_id) REFERENCES ssids (id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()