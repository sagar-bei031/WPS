import os
from enum import Enum

class Map(Enum):
    HOME = "myhome"
    ROBOTICS = "robotics"
    CLASS = "class"

class FilterType(Enum):
    NONE = None
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode" # Not implemented
    KALMAN = "kalman" # Not implemented yet

DB_FILE_NAME = Map.ROBOTICS.value + "_wifi.db"
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_FILE_PATH = os.path.join(PROJECT_DIR, DB_FILE_NAME)

SCANS_TO_ADD_SSID = 10
DELAY_BETWEEN_SCANS = 0.5
SCANS_FOR_FINGERPRINT = 100
RSS_FOR_UNREACHABLE = -100
USE_FILTERED_RSS = True
PREDICTION_FILTER_TYPE = FilterType.NONE