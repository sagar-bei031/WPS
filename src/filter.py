import sqlite3
import numpy as np
from statistics import mean, median, mode
from config import DB_FILE_PATH, FILTER, MOVING_AVERAGE_WINDOW, EXP_FILTER_ALPHA, AGGREGATION, USE_FILTER

def apply_moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def apply_exponential_filter(data, alpha):
    filtered_data = [data[0]]
    for i in range(1, len(data)):
        filtered_data.append(alpha * data[i] + (1 - alpha) * filtered_data[-1])
    return filtered_data

def aggregate_data(data, method):
    if method == "mean":
        return mean(data)
    elif method == "median":
        return median(data)
    elif method == "mode":
        return mode(data)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

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

    # Apply filter and aggregate
    filtered_aggregated_data = []
    for (location_id, ssid_id), rss_values in rss_data.items():
        if USE_FILTER:
            if FILTER == "moving_average":
                filtered_rss = apply_moving_average(rss_values, MOVING_AVERAGE_WINDOW)
            elif FILTER == "exponential":
                filtered_rss = apply_exponential_filter(rss_values, EXP_FILTER_ALPHA)
            else:
                filtered_rss = rss_values
        else:
            filtered_rss = rss_values

        aggregated_rss = aggregate_data(filtered_rss, AGGREGATION.value)
        sample_num = len(filtered_rss)
        var_rss = np.var(filtered_rss) if sample_num > 1 else 0

        filtered_aggregated_data.append((location_id, ssid_id, aggregated_rss, sample_num, var_rss))

    # Insert aggregated data into the `filtered_wifi_signals` table
    cursor.executemany("""
        INSERT INTO filtered_wifi_signals (location_id, ssid_id, agg_rss, sample_num, variance)
        VALUES (?, ?, ?, ?, ?)
    """, filtered_aggregated_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    filter_rss()
    print("RSS values have been filtered and stored in the `filtered_wifi_signals` table.")