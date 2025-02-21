import sys
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout, QPushButton, QScrollArea, QSplitter
from PyQt5.QtCore import Qt
from config import DB_FILE_PATH

class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSSI vs Position Plot")
        self.setGeometry(100, 100, 1200, 800)

        # Layouts
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Left panel for checkboxes
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.splitter.addWidget(self.left_widget)

        self.scroll_area = QScrollArea(self)
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.left_layout.addWidget(self.scroll_area)

        self.plot_button = QPushButton("Plot RSSI", self)
        self.plot_button.clicked.connect(self.plot_rssi_vs_position)
        self.left_layout.addWidget(self.plot_button)

        # Right panel for 3D plot
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.splitter.addWidget(self.right_widget)

        self.figure_3d = plt.figure(figsize=(8, 6))
        self.ax_3d = self.figure_3d.add_subplot(111, projection='3d')
        self.canvas_3d = FigureCanvas(self.figure_3d)
        self.right_layout.addWidget(self.canvas_3d)

        self.lines_3d = {}
        self.ssid_checkboxes = {}

        self.prepare_plot()

    def fetch_rssi_data(self):
        """Fetch filtered RSSI data from the database."""
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.ssid, s.bssid, f.agg_rss, l.x, l.y, l.floor
            FROM filtered_wifi_signals f
            JOIN ssids s ON f.ssid_id = s.id
            JOIN locations l ON f.location_id = l.id
            ORDER BY l.x, l.y, l.floor
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def prepare_plot(self):
        """Prepares the plot and checkboxes."""
        data = self.fetch_rssi_data()
        self.ssid_data = {}
        added_ssids = set()

        for ssid, bssid, rss, x, y, z in data:
            if bssid not in self.ssid_data:
                self.ssid_data[bssid] = {"ssid": ssid, "rss": [], "x": [], "y": [], "z": []}
            self.ssid_data[bssid]["rss"].append(rss)
            self.ssid_data[bssid]["x"].append(x)
            self.ssid_data[bssid]["y"].append(y)
            self.ssid_data[bssid]["z"].append(z)

        # Clear previous elements
        self.ax_3d.clear()
        self.lines_3d.clear()
        self.ssid_checkboxes.clear()

        # Add checkboxes dynamically
        for bssid, values in self.ssid_data.items():
            if (values['ssid'], bssid) not in added_ssids:
                checkbox = QCheckBox(f"{values['ssid']} ({bssid})", self.scroll_area_widget)
                checkbox.stateChanged.connect(self.toggle_visibility)
                self.scroll_area_layout.addWidget(checkbox)
                self.ssid_checkboxes[bssid] = checkbox
                added_ssids.add((values['ssid'], bssid))

        self.ax_3d.set_xlabel("X Coordinate")
        self.ax_3d.set_ylabel("Y Coordinate")
        self.ax_3d.set_zlabel("RSSI")
        self.ax_3d.set_title("RSSI vs X and Y Coordinates")

        self.canvas_3d.draw()

    def toggle_visibility(self):
        """Toggle the visibility of an SSID on the 3D plot."""
        checkbox = self.sender()
        label = checkbox.text()

        for bssid, values in self.ssid_data.items():
            if label == f"{values['ssid']} ({bssid})":
                if checkbox.isChecked():
                    norm = plt.Normalize(min(values["rss"]), max(values["rss"]))
                    
                    # **FIX: Pass RSSI as array for proper coloring**
                    self.lines_3d[bssid] = self.ax_3d.plot_trisurf(
                        values["x"], values["y"], values["rss"], 
                        cmap='viridis', norm=norm, linewidth=0.1, edgecolor='none'
                    )
                else:
                    self.lines_3d[bssid].remove()
                    del self.lines_3d[bssid]

                self.canvas_3d.draw()

    def plot_rssi_vs_position(self):
        """Plot all SSIDs on the 3D plot with proper gradient coloring."""
        self.ax_3d.clear()

        for bssid, values in self.ssid_data.items():
            norm = plt.Normalize(min(values["rss"]), max(values["rss"]))

            # **FIX: Remove facecolors & use RSSI as array to get smooth gradient**
            self.lines_3d[bssid] = self.ax_3d.plot_trisurf(
                values["x"], values["y"], values["rss"], 
                cmap='viridis', norm=norm, linewidth=0.1, edgecolor='none'
            )

            if bssid in self.ssid_checkboxes:
                self.ssid_checkboxes[bssid].setChecked(True)

        self.ax_3d.set_xlabel("X Coordinate")
        self.ax_3d.set_ylabel("Y Coordinate")
        self.ax_3d.set_zlabel("RSSI")
        self.ax_3d.set_title("RSSI vs X and Y Coordinates")

        self.canvas_3d.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())
