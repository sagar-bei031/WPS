import pywifi
from pywifi import const

def scan_wifi():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0] 
    iface.scan()
    results = iface.scan_results()

    for network in results:
        print(f"SSID: {network.ssid}, BSSID: {network.bssid}, RSSI: {network.signal}")

scan_wifi()
