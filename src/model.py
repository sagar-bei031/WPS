import sqlite3
from config import DB_FILE_PATH

def initialize_database():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect(DB_FILE_PATH)
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
            appeared_count INTEGER DEFAULT 0,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create the `scans` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pass_id INTEGER,
            scan_time DATETIME,
            FOREIGN KEY (pass_id) REFERENCES scan_passes (id)
        )
    """)
    # Create the `scan_passes` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            pass_time DATETIME,
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
    """)

    # Create the `wifi_signals` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wifi_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            ssid_id INTEGER,
            rss INTEGER,
            FOREIGN KEY (scan_id) REFERENCES scans (id),
            FOREIGN KEY (ssid_id) REFERENCES ssids (id)
        )
    """)

    # Create the `filtered_wifi_signals` table without `scan_id`
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filtered_wifi_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            ssid_id INTEGER,
            agg_rss INTEGER,
            sample_num INTEGER,
            variance REAL,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (ssid_id) REFERENCES ssids (id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()