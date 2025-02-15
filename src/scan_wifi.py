from pywifi import PyWiFi

def scan_wifi(scan_count=10):
    """Scan available Wi-Fi networks multiple times and return aggregated details."""
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Get the first wireless interface
    networks = {}

    print("Scanning for networks", end="", flush=True)
    for _ in range(scan_count):
        print(".", end="", flush=True)
        iface.scan()
        scan_results = iface.scan_results()
        seen_networks = set()

        for result in scan_results:
            ssid = result.ssid
            bssid = result.bssid
            rssi = result.signal

            if (ssid, bssid) not in seen_networks:
                seen_networks.add((ssid, bssid))
                if (ssid, bssid) in networks:
                    networks[(ssid, bssid)]['rssi_sum'] += rssi
                    networks[(ssid, bssid)]['count'] += 1
                else:
                    networks[(ssid, bssid)] = {'rssi_sum': rssi, 'count': 1}

    print("\nScan complete.")

    aggregated_networks = []
    for (ssid, bssid), data in networks.items():
        avg_rssi = data['rssi_sum'] / data['count']
        aggregated_networks.append((ssid, bssid, avg_rssi, data['count']))

    return aggregated_networks