import subprocess
import re

def percentage_to_dbm(percentage):
    """Convert signal strength from percentage to dBm."""
    return (percentage / 2) - 100

def scan_wifi(scan_count=10, verbose=False):
    """Scan available Wi-Fi networks multiple times and return aggregated details."""
    networks = {}

    for _ in range(scan_count):
        if verbose:
            print("Scanning for networks...", end="", flush=True)

        # Run the netsh command to scan Wi-Fi networks
        result = subprocess.run(["netsh", "wlan", "show", "network", "mode=Bssid"], capture_output=True, text=True)
        output = result.stdout

        # Debugging: Print the raw output of the netsh command
        if verbose:
            print("Raw output of netsh command:")
            print(output)

        # Parse the output to extract SSID, BSSID, and RSSI
        ssid = None
        for line in output.split("\n"):
            ssid_match = re.search(r"SSID\s+\d+\s+:\s+(.*)", line)
            bssid_match = re.search(r"BSSID\s+\d+\s+:\s+([0-9A-Fa-f:]+)", line)
            rssi_match = re.search(r"Signal\s+:\s+(\d+)%", line)

            if ssid_match:
                ssid = ssid_match.group(1).strip()
            elif bssid_match and ssid:
                bssid = bssid_match.group(1).strip()
                rssi_percentage = int(rssi_match.group(1)) if rssi_match else None

                if rssi_percentage is not None:
                    rssi_dbm = percentage_to_dbm(rssi_percentage)
                    if (ssid, bssid) not in networks:
                        networks[(ssid, bssid)] = {'rssi_sum': 0, 'count': 0}
                    networks[(ssid, bssid)]['rssi_sum'] += rssi_dbm
                    networks[(ssid, bssid)]['count'] += 1

        if verbose:
            print(" Done")

    # Calculate the average RSSI for each network
    aggregated_networks = []
    for (ssid, bssid), data in networks.items():
        avg_rssi = data['rssi_sum'] / data['count']
        aggregated_networks.append((ssid, bssid, avg_rssi, data['count']))

    return aggregated_networks