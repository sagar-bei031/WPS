import re
import subprocess

def get_wifi_networks():
    command = "netsh wlan show networks mode=bssid"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    output = result.stdout

    print(output)  # Debug: Print raw output to check formatting

    networks = []
    network = None

    for line in output.splitlines():
        line = line.strip()

        ssid_match = re.match(r"^SSID\s+\d+\s+:\s+(.+)", line)
        if ssid_match:
            if network:
                networks.append(network)
            network = {"SSID": ssid_match.group(1), "BSSIDs": []}

        if network:
            bssid_match = re.match(r"^BSSID\s+\d+\s+:\s+([0-9A-Fa-f:-]+)", line)
            if bssid_match:
                network["BSSIDs"].append({"BSSID": bssid_match.group(1)})

            signal_match = re.match(r"^Signal\s+:\s+(\d+)%", line)
            if signal_match and network["BSSIDs"]:
                network["BSSIDs"][-1]["Signal"] = signal_match.group(1)

            channel_match = re.match(r"^Channel\s+:\s+(\d+)", line)
            if channel_match and network["BSSIDs"]:
                network["BSSIDs"][-1]["Channel"] = int(channel_match.group(1))

            radio_match = re.match(r"^Radio type\s+:\s+(.+)", line)
            if radio_match and network["BSSIDs"]:
                network["BSSIDs"][-1]["Radio Type"] = radio_match.group(1)

            band_match = re.match(r"^Band\s+:\s+(.+)", line)
            if band_match and network["BSSIDs"]:
                network["BSSIDs"][-1]["Band"] = band_match.group(1)

    if network:
        networks.append(network)

    return networks

if __name__ == "__main__":
    wifi_networks = get_wifi_networks()
    for network in wifi_networks:
        print(f"SSID: {network['SSID']}")
        for bssid in network["BSSIDs"]:
            print(f"  BSSID: {bssid['BSSID']}, Signal: {bssid.get('Signal', 'N/A')}%, "
                  f"Channel: {bssid.get('Channel', 'N/A')}, Radio: {bssid.get('Radio Type', 'N/A')}, "
                  f"Band: {bssid.get('Band', 'N/A')}")
        print()
