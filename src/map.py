import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
from predict import init_prediction, predict_location
from config import FILTER, K, USE_AGGREGATION

def get_test_position():
    # Simulate getting a new position
    x, y, z = np.random.rand(), np.random.rand(), 1
    print(f"Position: ({x:.2f}, {y:.2f}, {z:.2f})")
    return x, y, z

stl_file = "MyRoom.stl"
mesh = trimesh.load_mesh(stl_file)

# Adjust coordinate system
vertices = mesh.vertices[:, [0, 2, 1]]
vertices = -vertices

faces = mesh.faces
xmin, ymin, zmin = np.min(vertices, axis=0)
xmax, ymax, zmax = np.max(vertices, axis=0)
print(f"X: {xmin:.2f} to {xmax:.2f}")
print(f"Y: {ymin:.2f} to {ymax:.2f}")
print(f"Z: {zmin:.2f} to {zmax:.2f}")

def get_map_x(x):
    return x * 6000 - 6000

def get_map_y(y):
    return y * 4000 - 4000

def get_map_z(z):
    return -z * 810

# Create figure and 3D axis
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Plot STL
ax.add_collection3d(Poly3DCollection(vertices[faces], alpha=0.3, edgecolor='k'))

# Initial location point
location_point, = ax.plot([get_map_x(0.5)], [get_map_y(0.5)], [get_map_z(0)], 'ro', markersize=10, label='Location Point')
print(f"Initial Location: ({get_map_x(0.5):.2f}, {get_map_y(0.5):.2f}, {get_map_z(0):.2f})")

# Add text label outside the graph
text_label = ax.text2D(0.00, 1.0, f"(0.50, 0.50, 0.00)", transform=ax.transAxes, color='black', fontsize=10, verticalalignment='top')

# Set axis limits
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_zlim(zmin, zmax)

# Fix aspect ratio
ax.set_box_aspect([xmax - xmin, ymax - ymin, zmax - zmin])

# **Set Initial View (Top Perspective according to STL)**
DEFAULT_ELEV, DEFAULT_AZIM, DEFAUT_ROLL = -90, 0, 0
angle_elev, angle_azim, angle_roll = DEFAULT_ELEV, DEFAULT_AZIM, DEFAUT_ROLL
ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)

# Labels and legend
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.legend()

# Hide axis labels initially
ax.set_xticks([]), ax.set_yticks([]), ax.set_zticks([])
ax.set_xticklabels([]), ax.set_yticklabels([]), ax.set_zticklabels([])
ax.grid(False)

axes_visible = False

# --- Button Functions ---
rotation_step = 10

def inx_elev(event):
    global angle_elev
    angle_elev += rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def dcx_elev(event):
    global angle_elev
    angle_elev -= rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def inx_azim(event):
    global angle_azim
    angle_azim += rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def dcx_azim(event):
    global angle_azim
    angle_azim -= rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def inx_roll(event):
    global angle_roll
    angle_roll += rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def dcx_roll(event):
    global angle_roll
    angle_roll -= rotation_step
    ax.view_init(elev=angle_elev, azim=angle_azim, roll=angle_roll)
    plt.draw()

def toggle_axes(event):
    global axes_visible
    if axes_visible:
        ax.set_xticks([]), ax.set_yticks([]), ax.set_zticks([])
        ax.set_xticklabels([]), ax.set_yticklabels([]), ax.set_zticklabels([])
        ax.grid(False)
    else:
        ax.set_xticks(np.linspace(xmin, xmax, 5))
        ax.set_yticks(np.linspace(ymin, ymax, 5))
        ax.set_zticks(np.linspace(zmin, zmax, 2))

        ax.set_xticklabels([f"{x:.2f}" for x in np.linspace(0, 1, 5)])
        ax.set_yticklabels([f"{y:.2f}" for y in np.linspace(0, 1, 5)])
        ax.set_zticklabels([f"{z:.2f}" for z in np.linspace(1, 0, 2)])

        ax.grid(True)

    axes_visible = not axes_visible
    plt.draw()

button_width, button_height = 0.1, 0.05  
start_x, start_y = 0.1, 0.9  

ax_azim_p = plt.axes([start_x, start_y, button_width, button_height])
ax_azim_m = plt.axes([start_x + 0.1, start_y, button_width, button_height])
ax_elev_p = plt.axes([start_x + 0.2, start_y, button_width, button_height])
ax_elev_m = plt.axes([start_x + 0.3, start_y, button_width, button_height])
ax_roll_p = plt.axes([start_x + 0.4, start_y, button_width, button_height])
ax_roll_m = plt.axes([start_x + 0.5, start_y, button_width, button_height])
ax_axes = plt.axes([start_x + 0.6, start_y, button_width, button_height])

btn_azim_p = Button(ax_azim_p, "Azim+")
btn_azim_m = Button(ax_azim_m, "Azim-")
btn_elev_p = Button(ax_elev_p, "Elev+")
btn_elev_m = Button(ax_elev_m, "Elev-")
btn_roll_p = Button(ax_roll_p, "Roll+")
btn_roll_m = Button(ax_roll_m, "Roll-")
btn_axes = Button(ax_axes, "Toggle Axes")

btn_azim_p.on_clicked(inx_azim)
btn_azim_m.on_clicked(dcx_azim)
btn_elev_p.on_clicked(inx_elev)
btn_elev_m.on_clicked(dcx_elev)
btn_roll_p.on_clicked(inx_roll)
btn_roll_m.on_clicked(dcx_roll)
btn_axes.on_clicked(toggle_axes)

structured_fingerprints =  init_prediction()

def update(frame):
    x, y, floor = predict_location(structured_fingerprints, filter_type=FILTER, k=K, use_aggregation=USE_AGGREGATION)
    location_point.set_data_3d([get_map_x(x)], [get_map_y(y)], [get_map_z(floor)])
    text_label.set_text(f"({x:.2f}, {y:.2f}, {floor:.2f})")
    return location_point, text_label

ani = FuncAnimation(fig, update, interval=100, cache_frame_data=False)

plt.show()