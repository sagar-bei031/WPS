import os

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DB_FILE_PATH = os.path.join(PROJECT_DIR, "myhome_wifi.db")
TOTAL_SCANS_FOR_FINGERPRINT = 1000