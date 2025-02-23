import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QCheckBox, QHBoxLayout, QPushButton, QScrollArea, QSplitter
from PyQt5.QtCore import Qt, QTimer
from config import EXP_FILTER_ALPHA, MOVING_AVERAGE_WINDOW, DELAY_BETWEEN_SCANS

from network import get_networks

WINDOW_TIME = 20  # Window time in seconds

class RealTimePlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time RSSI Plot")
        self.setGeometry(100, 100, 1200, 600)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)

        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidgetResizable(True)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_scroll_area.setWidget(self.left_widget)
        self.splitter.addWidget(self.left_scroll_area)

        self.filter_dropdown = QComboBox(self)
        self.filter_dropdown.addItems(["Raw", "Moving Average", "Exponential"])
        self.left_layout.addWidget(self.filter_dropdown)

        self.apply_button = QPushButton("Apply Filter", self)
        self.apply_button.clicked.connect(self.apply_filter)
        self.left_layout.addWidget(self.apply_button)

        self.select_all_button = QPushButton("Select All", self)
        self.select_all_button.clicked.connect(self.select_all)
        self.left_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton("Deselect All", self)
        self.deselect_all_button.clicked.connect(self.deselect_all)
        self.left_layout.addWidget(self.deselect_all_button)

        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.splitter.addWidget(self.right_widget)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)

        self.lines = {}
        self.ssid_checkboxes = {}
        self.ssid_data = {}
        self.start_time = time.time()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(DELAY_BETWEEN_SCANS * 1000))

    def update_plot(self):
        current_time = time.time() - self.start_time
        networks = get_networks()
        for network in networks:
            ssid = network["ssid"]
            bssid = network["bssid"]
            rss = network["rss"]

            if bssid not in self.ssid_data:
                self.ssid_data[bssid] = {"ssid": ssid, "rss": [], "time": []}
                line, = self.ax.plot([], [], label=f"{ssid} ({bssid})", visible=False)
                self.lines[bssid] = line
                checkbox = QCheckBox(f"{ssid} ({bssid})", self)
                checkbox.setChecked(False)
                checkbox.stateChanged.connect(self.toggle_visibility)
                self.left_layout.addWidget(checkbox)
                self.ssid_checkboxes[bssid] = checkbox

            self.ssid_data[bssid]["rss"].append(rss)
            self.ssid_data[bssid]["time"].append(current_time)

            # Keep only the data within the window time
            while self.ssid_data[bssid]["time"] and self.ssid_data[bssid]["time"][0] < current_time - WINDOW_TIME:
                self.ssid_data[bssid]["time"].pop(0)
                self.ssid_data[bssid]["rss"].pop(0)

        self.apply_filter()

    def toggle_visibility(self):
        checkbox = self.sender()
        label = checkbox.text()
        for bssid, values in self.ssid_data.items():
            if label == f"{values['ssid']} ({bssid})":
                line = self.lines[bssid]
                line.set_visible(checkbox.isChecked())
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
        self.ax.set_xlim(max(0, time.time() - self.start_time - WINDOW_TIME), time.time() - self.start_time)
        self.update_legend()
        self.canvas.draw()

    def update_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        visible_handles = [handle for handle, label in zip(handles, labels) if handle.get_visible()]
        visible_labels = [label for handle, label in zip(handles, labels) if handle.get_visible()]
        self.ax.legend(visible_handles, visible_labels)

    def select_all(self):
        for checkbox in self.ssid_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        for checkbox in self.ssid_checkboxes.values():
            checkbox.setChecked(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RealTimePlotWindow()
    window.show()
    sys.exit(app.exec_())