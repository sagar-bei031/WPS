import re
import subprocess
from time import sleep
from statistics import median, variance
from config import DELAY_BETWEEN_SCANS
from pywifi import PyWiFi, const

USE_PI_WIFI = True

def get_rss(signal):
    """
    Convert the signal strength to an RSS value.
    """
    signal = int(signal)
    if signal <= 0:
        return -100
    elif signal >= 100:
        return -50
    else:
        return signal / 2 - 100

def scan_wifi_networks_netsh():
    command = "netsh wlan show networks mode=bssid"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    output = result.stdout
    
    networks = []
    network = None

    for line in output.splitlines():
        line = line.strip()

        ssid_match = re.match(r"^SSID\s+\d+\s+:\s*(.*)", line)
        if ssid_match:
            ssid = ssid_match.group(1).strip()
            if network:
                networks.append(network)
            network = {"SSID": ssid if ssid else "", "BSSIDs": []}

        if network:
            bssid_match = re.match(r"^BSSID\s+\d+\s+:\s+([0-9A-Fa-f:-]+)", line)
            if bssid_match:
                network["BSSIDs"].append({"BSSID": bssid_match.group(1)})

            signal_match = re.match(r"^Signal\s+:\s+(\d+)%", line)
            if signal_match and network["BSSIDs"][-1]:
                network["BSSIDs"][-1]["Signal"] = int(signal_match.group(1))

            channel_match = re.match(r"^Channel\s+:\s+(\d+)", line)
            if channel_match and network["BSSIDs"][-1]:
                network["BSSIDs"][-1]["Channel"] = int(channel_match.group(1))

            radio_match = re.match(r"^Radio type\s+:\s+(.+)", line)
            if radio_match and network["BSSIDs"][-1]:
                network["BSSIDs"][-1]["Radio Type"] = radio_match.group(1)

            band_match = re.match(r"^Band\s+:\s+(.+)", line)
            if band_match and network["BSSIDs"][-1]:
                network["BSSIDs"][-1]["Band"] = band_match.group(1)

    if network:
        networks.append(network)

    return get_minimal_networks(networks)

def get_minimal_networks(networks):
    """
    Convert the network data to a minimal format {ssid, bssid, rss}.
    """
    minimal_networks = []
    for network in networks:
        ssid = network["SSID"]
        for bssid_info in network["BSSIDs"]:
            minimal_networks.append({
                "ssid": ssid,
                "bssid": bssid_info["BSSID"],
                "rss": get_rss(bssid_info["Signal"])
            })
    return minimal_networks

def scan_wifi_networks_piwifi():
    """Scan available Wi-Fi networks."""
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]  # Get the first wireless interface
    iface.scan()
    # sleep(2)  # Wait for scan results
    results = iface.scan_results()

    networks = []

    for result in results:
        ssid = result.ssid
        bssid = result.bssid[:-1] # Remove ':' from the end
        rss = result.signal
        networks.append({
            "ssid": ssid, 
            "bssid": bssid, 
            "rss": rss  # Use the raw signal value directly
        })

    return networks

def get_networks():
    """
    Process the list of networks and return them in the format {ssid, bssid, rss}.
    """
    if USE_PI_WIFI:
        return scan_wifi_networks_piwifi()
    else:
        return scan_wifi_networks_netsh()

def get_networks_with_mean_rss(scan_count=10, sleep_time=DELAY_BETWEEN_SCANS):
    """
    Get the average rss of the networks over multiple scans.
    """
    avg_networks = []
    rss_data = {}
    for _ in range(scan_count):
        networks = get_networks()
        for network in networks:
            ssid = network["ssid"]
            bssid = network["bssid"]
            rss = network["rss"]
            if (ssid, bssid) not in rss_data:
                rss_data[(ssid, bssid)] = []
            rss_data[(ssid, bssid)].append(rss)
            found = False
            for avg_network in avg_networks:
                if avg_network["ssid"] == ssid and avg_network["bssid"] == bssid:
                    avg_network["rss"] += rss
                    avg_network["count"] += 1
                    found = True
                    break
            if not found:
                avg_networks.append({"ssid": ssid, "bssid": bssid, "rss": rss, "count": 1})
        sleep(sleep_time)

    for avg_network in avg_networks:
        avg_network["rss"] /= avg_network["count"]
        if len(rss_data[(avg_network["ssid"], avg_network["bssid"])]) > 1:
            avg_network["variance"] = variance(rss_data[(avg_network["ssid"], avg_network["bssid"])])
        else:
            avg_network["variance"] = 0

    return avg_networks

def get_networks_with_median_rss(scan_count=10, sleep_time=DELAY_BETWEEN_SCANS):
    """
    Get the median rss of the networks over multiple scans.
    """
    rss_data = {}
    for _ in range(scan_count):
        networks = get_networks()
        for network in networks:
            ssid = network["ssid"]
            bssid = network["bssid"]
            rss = network["rss"]
            if (ssid, bssid) not in rss_data:
                rss_data[(ssid, bssid)] = []
            rss_data[(ssid, bssid)].append(rss)
        sleep(sleep_time)

    median_networks = []
    for (ssid, bssid), rss in rss_data.items():
        median_networks.append({
            "ssid": ssid,
            "bssid": bssid,
            "rss": median(rss),
            "count": len(rss),
            "variance": variance(rss) if len(rss) > 1 else 0
        })

    return median_networks

if __name__ == "__main__":
    networks = get_networks()
    if networks:
        print(f"Found {len(networks)} {'network' if len(networks) == 1 else 'networks'}:")
        for network in networks:
            print(network)
    else:
        print("No networks found.")