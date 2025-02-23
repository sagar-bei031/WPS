import os
from enum import Enum

class Map(Enum):
    HOME = "myhome"
    ROBOTICS = "robotics"
    CLASS = "class"

class FilterType(Enum):
    NONE = None
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL = "exponential"
    KALMAN = "kalman" # Not implemented yet

class AggregationType(Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"

DB_FILE_NAME = Map.ROBOTICS.value + "_wifi.db"
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_FILE_PATH = os.path.join(PROJECT_DIR, DB_FILE_NAME)

SCANS_TO_ADD_SSID = 10
DELAY_BETWEEN_SCANS = 0.5
SCANS_FOR_FINGERPRINT = 100
RSS_FOR_UNREACHABLE = -95

FILTER = FilterType.MOVING_AVERAGE
MOVING_AVERAGE_WINDOW = 3
EXP_FILTER_ALPHA = 0.2

AGGREGATION = AggregationType.MEDIAN
USE_AGGREGATION = True

INTERPOLATION_METHOD = 'cubic'  # Options: 'linear', 'nearest', 'cubic'
USE_INTERPOLATION = True # Used for plotting only
USE_FILTER = True

K = 3
STRUCTURED_FINGERPRINTS_FILE = "structured_fingerprints.csv"
PLOT_GRAPH_WHILE_SCANNING = True