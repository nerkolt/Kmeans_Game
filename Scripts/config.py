"""
Central configuration/constants for the clustering visualizer.
Keeping this separate makes the rest of the code easier to read and change.
"""

# Window
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Layout
UI_PANEL_HEIGHT = 140  # bottom UI bar height
TOP_MARGIN = 80
SIDE_MARGIN = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Modern color palette (softer, more aesthetic)
COLORS = [
    (255, 107, 107),  # Coral Red
    (78, 205, 196),   # Turquoise
    (255, 159, 243),  # Pink
    (255, 195, 113),  # Peach
    (162, 155, 254),  # Lavender
]

BG_COLOR = (32, 32, 42)  # Dark blue-gray background
UI_BG = (45, 45, 58)
TEXT_COLOR = (220, 220, 230)

