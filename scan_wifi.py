from pywifi import PyWiFi


def scan_wifi():
    """Scan available Wi-Fi networks and return details."""
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Get the first wireless interface
    iface.scan()
    print("Scanning for networks...")
    scan_results = iface.scan_results()
    networks = []
    for result in scan_results:
        ssid = result.ssid
        bssid = result.bssid
        rssi = result.signal
        networks.append((ssid, bssid, rssi))
    return networks