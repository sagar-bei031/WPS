import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from network import get_networks

def test_network():
    networks = get_networks()

    if networks:
        print(f"Found {len(networks)} {'network' if len(networks) == 1 else 'networks'}:")
    else:
        print("No networks found.")
        
    for network in networks:
        print(network)

def test_network_stability(ssid, bssid):
    try:
        while True:
            networks = get_networks()
            if networks:
                for network in networks:
                    if network["ssid"] == ssid and network["bssid"] == bssid:
                        print(network)    
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    # test_network()
    test_network_stability("kritish1_5", "40:e1:e4:0e:6a:5e")