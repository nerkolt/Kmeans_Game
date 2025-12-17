"""
Central configuration/constants for the clustering visualizer.

Note: Some settings (window size + color palette) can be changed at runtime
from the Start/Options menu. For that reason, other modules should prefer
`import config` and read `config.WIDTH`, `config.HEIGHT`, `config.COLORS`, etc.
instead of importing the values directly.
"""

# Window (default)
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Layout
UI_PANEL_HEIGHT = 140  # bottom UI bar height
TOP_MARGIN = 80
SIDE_MARGIN = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Palettes
DEFAULT_COLORS = [
    (255, 107, 107),  # Coral Red
    (78, 205, 196),   # Turquoise
    (255, 159, 243),  # Pink
    (255, 195, 113),  # Peach
    (162, 155, 254),  # Lavender
    (255, 214, 102),  # Warm Yellow
    (95, 168, 211),   # Sky Blue
    (99, 212, 113),   # Mint Green
    (255, 140, 82),   # Orange
    (46, 134, 222),   # Blue
    (0, 184, 148),    # Teal Green
    (225, 112, 85),   # Terracotta
    (108, 92, 231),   # Deep Purple
    (9, 132, 227),    # Azure
    (253, 121, 168),  # Rose
    (0, 206, 201),    # Cyan
    (214, 48, 49),    # Red
]

# Colorblind-friendly palette (Okabe-Ito inspired + a few extras)
# High contrast, less reliance on red/green separation.
COLORBLIND_COLORS = [
    (0, 114, 178),    # Blue
    (230, 159, 0),    # Orange
    (0, 158, 115),    # Bluish Green
    (204, 121, 167),  # Reddish Purple
    (86, 180, 233),   # Sky Blue
    (213, 94, 0),     # Vermillion
    (240, 228, 66),   # Yellow
    (160, 160, 160),  # Gray
    (0, 0, 0),        # Black
]

# Active palette (default)
COLORS = list(DEFAULT_COLORS)


def set_palette(mode: str) -> None:
    """
    Switch the active cluster palette.
    mode: "default" | "colorblind"
    """
    global COLORS
    if str(mode).lower().startswith("color"):
        COLORS = list(COLORBLIND_COLORS)
    else:
        COLORS = list(DEFAULT_COLORS)

BG_COLOR = (32, 32, 42)  # Dark blue-gray background
UI_BG = (45, 45, 58)
TEXT_COLOR = (220, 220, 230)

