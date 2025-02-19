import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DB_FILE_PATH = os.path.join(PROJECT_DIR, "myhome_wifi.db")

SCANS_FOR_ONE_FINGERPRINT = 1
FINGERPRINTS_FOR_ONE_LOCATION = 1000
DELAY_BETWEEN_SCANS = 0.5
SCANS_TO_ADD_SSID = 10