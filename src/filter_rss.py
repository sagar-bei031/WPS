import sqlite3
from statistics import mean, variance
from config import DB_FILE_PATH

def filter_rss():
    """Filter RSS values from the database and store them in the `filtered_wifi_signals` table."""
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    # Erase all data from the `filtered_wifi_signals` table
    cursor.execute("DELETE FROM filtered_wifi_signals;")

    # Retrieve all RSS values from the `wifi_signals` table
    cursor.execute("""
        SELECT w.scan_id, w.ssid_id, w.rss, sc.session_id, ss.location_id
        FROM wifi_signals w
        JOIN scans sc ON w.scan_id = sc.id
        JOIN scan_sessions ss ON sc.session_id = ss.id
    """)
    wifi_signals = cursor.fetchall()

    # Aggregate RSS values by location_id and ssid_id
    rss_data = {}
    for scan_id, ssid_id, rss, session_id, location_id in wifi_signals:
        key = (location_id, ssid_id)
        if key not in rss_data:
            rss_data[key] = []
        rss_data[key].append(rss)

    # Insert aggregated data into the `filtered_wifi_signals` table
    for (location_id, ssid_id), rss_list in rss_data.items():
        avg_rss = mean(rss_list)
        var_rss = variance(rss_list) if len(rss_list) > 1 else 0
        sample_num = len(rss_list)

        cursor.execute("""
            INSERT INTO filtered_wifi_signals (location_id, ssid_id, agg_rss, sample_num, variance)
            VALUES (?, ?, ?, ?, ?)
        """, (location_id, ssid_id, avg_rss, sample_num, var_rss))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    filter_rss()
    print("RSS values have been filtered and stored in the `filtered_wifi_signals` table.")