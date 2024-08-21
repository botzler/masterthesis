import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import hsv_to_rgb

# Define the HSV values for the left and right edges
hsv1 = [0.0, 1.0, 1.0]  # HSV for (-1, 0)
hsv2 = [0.2, 1.0, 1.0]  # HSV for (1, 0)
mood = [0.8, 0.7]       # Example mood values

# Create a grid of x and y values
x = np.linspace(-1, 1, 500)
y = np.linspace(-1, 1, 500)
X, Y = np.meshgrid(x, y)

# Calculate HSV values across the grid
H = ((hsv2[0] - hsv1[0]) / 2) * (X + 1) + hsv1[0]
S = ((hsv2[1] - hsv1[1]) / 2) * (X + 1) + hsv1[1]
V = 45 * mood[0] * Y + 55

# Normalize V to be between 0 and 1 for hsv_to_rgb conversion
V = np.clip(V / 100.0, 0, 1)

# Convert HSV to RGB
RGB = hsv_to_rgb(np.stack((H, S, V), axis=-1))

# Create the plot
fig, ax = plt.subplots(figsize=(6, 6))

# Display the background as an image
ax.imshow(RGB, extent=(-1, 1, -1, 1), origin='lower')

# Plot a coordinate system ranging from -1 to 1
ax.axhline(0, color='black', linewidth=0.8)
ax.axvline(0, color='black', linewidth=0.8)

# Set the limits and ticks
ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_xticks(np.arange(-1, 1.1, 0.5))
ax.set_yticks(np.arange(-1, 1.1, 0.5))

# Add grid lines for better visibility
ax.grid(True, linestyle='--', linewidth=0.5)

# Label the axes
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')

# Show the plot
plt.title("Mood color interpolation")
plt.show()
