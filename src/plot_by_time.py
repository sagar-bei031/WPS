import sys
import sqlite3
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QCheckBox, QHBoxLayout, QPushButton, QScrollArea, QSplitter
from PyQt5.QtCore import Qt
from config import DB_FILE_PATH, EXP_FILTER_ALPHA, MOVING_AVERAGE_WINDOW

class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSSI vs Time Plot")
        self.setGeometry(100, 100, 1200, 600)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)

        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.splitter.addWidget(self.left_widget)

        self.location_dropdown = QComboBox(self)
        self.location_dropdown.currentIndexChanged.connect(self.on_location_select)
        self.left_layout.addWidget(self.location_dropdown)

        self.scroll_area = QScrollArea(self)
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.left_layout.addWidget(self.scroll_area)

        self.filter_dropdown = QComboBox(self)
        self.filter_dropdown.addItems(["Raw", "Moving Average", "Exponential"])
        self.left_layout.addWidget(self.filter_dropdown)

        self.apply_button = QPushButton("Apply Filter", self)
        self.apply_button.clicked.connect(self.apply_filter)
        self.left_layout.addWidget(self.apply_button)

        self.plot_button = QPushButton("Plot RSSI", self)
        self.plot_button.clicked.connect(self.plot_rssi_vs_time)
        self.left_layout.addWidget(self.plot_button)

        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.splitter.addWidget(self.right_widget)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)

        self.lines = {}
        self.ssid_checkboxes = {}

        self.load_locations()

    def load_locations(self):
        locations = self.fetch_locations()
        for loc in locations:
            self.location_dropdown.addItem(f"ID: {loc[0]}, Name: {loc[4]}", loc[0])

    def fetch_locations(self):
        """Fetch all locations from the database."""
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, x, y, floor, location_name FROM locations")
        locations = cursor.fetchall()
        conn.close()
        return locations

    def fetch_rssi_data(self, location_id):
        """Fetch RSSI data from the database for a specific location."""
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.ssid, s.bssid, w.rss, sc.scan_time
            FROM wifi_signals w
            JOIN scans sc ON w.scan_id = sc.id
            JOIN ssids s ON w.ssid_id = s.id
            JOIN scan_sessions ss ON sc.session_id = ss.id
            WHERE ss.location_id = ?
            ORDER BY sc.scan_time
        """, (location_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def on_location_select(self):
        location_id = self.location_dropdown.currentData()
        data = self.fetch_rssi_data(location_id)
        if data:
            self.prepare_plot(data)
        else:
            print("No data found for the selected location.")

    def prepare_plot(self, data):
        self.ssid_data = {}
        added_ssids = set()
        for ssid, bssid, rss, scan_time in data:
            if bssid not in self.ssid_data:
                self.ssid_data[bssid] = {"ssid": ssid, "rss": [], "time": []}
            self.ssid_data[bssid]["rss"].append(rss)
            self.ssid_data[bssid]["time"].append(datetime.strptime(scan_time, "%Y-%m-%d %H:%M:%S"))

        self.ax.clear()
        self.lines.clear()
        self.ssid_checkboxes.clear()
        for bssid, values in self.ssid_data.items():
            if (values['ssid'], bssid) not in added_ssids:
                line, = self.ax.plot(values["time"], values["rss"], label=f"{values['ssid']} ({bssid})", visible=True)
                self.lines[bssid] = line
                checkbox = QCheckBox(f"{values['ssid']} ({bssid})", self.scroll_area_widget)
                checkbox.stateChanged.connect(self.toggle_visibility)
                self.scroll_area_layout.addWidget(checkbox)
                self.ssid_checkboxes[bssid] = checkbox
                added_ssids.add((values['ssid'], bssid))

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("RSSI")
        self.ax.set_title("RSSI vs Time for each SSID")
        self.update_legend()
        self.canvas.draw()

    def toggle_visibility(self):
        checkbox = self.sender()
        label = checkbox.text()
        for bssid, values in self.ssid_data.items():
            if label == f"{values['ssid']} ({bssid})":
                line = self.lines[bssid]
                line.set_visible(checkbox.isChecked())
                self.update_legend()
                self.canvas.draw()

    def plot_rssi_vs_time(self):
        for checkbox in self.ssid_checkboxes.values():
            checkbox.setChecked(True)
        self.update_legend()
        self.canvas.draw()

    def apply_moving_average(self, data, window_size=MOVING_AVERAGE_WINDOW):
        return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

    def apply_exponential_filter(self, data, alpha=EXP_FILTER_ALPHA):
        filtered_data = [data[0]]
        for i in range(1, len(data)):
            filtered_data.append(alpha * data[i] + (1 - alpha) * filtered_data[-1])
        return filtered_data

    def apply_filter(self):
        filter_type = self.filter_dropdown.currentText()
        for bssid, values in self.ssid_data.items():
            if filter_type == "Moving Average":
                filtered_data = self.apply_moving_average(values["rss"])
                filtered_time = values["time"][:len(filtered_data)]
            elif filter_type == "Exponential":
                filtered_data = self.apply_exponential_filter(values["rss"])
                filtered_time = values["time"]
            else:
                filtered_data = values["rss"]
                filtered_time = values["time"]

            self.lines[bssid].set_data(filtered_time, filtered_data)
            self.lines[bssid].set_visible(self.ssid_checkboxes[bssid].isChecked())

        self.ax.relim()
        self.ax.autoscale_view()
        self.update_legend()
        self.canvas.draw()

    def update_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        visible_handles = [handle for handle, label in zip(handles, labels) if handle.get_visible()]
        visible_labels = [label for handle, label in zip(handles, labels) if handle.get_visible()]
        self.ax.legend(visible_handles, visible_labels)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())