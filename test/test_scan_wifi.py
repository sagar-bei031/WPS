import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import scan_wifi

def test_scan_wifi():
    networks = scan_wifi.scan_wifi(scan_count=1, verbose=True)

    if networks:
        print(f"Found {len(networks)} {'network' if len(networks) == 1 else 'networks'}:")
    else:
        print("No networks found.")
        
    for network in networks:
        print(network)

if __name__ == "__main__":
    test_scan_wifi()