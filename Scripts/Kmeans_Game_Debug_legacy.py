import pygame
import random
import math
import csv
import os
import time

# Initialize Pygame
pygame.init()

# Constants
# Bigger window so UI fits comfortably
WIDTH, HEIGHT = 1200, 800
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Layout
UI_PANEL_HEIGHT = 140  # bottom UI bar height
TOP_MARGIN = 80
SIDE_MARGIN = 80

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

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.cluster = None
        self.prev_cluster = None
        self.transition = 0  # For color transitions
        self.scale = 1.0
        self.trail = []  # Position history for trails
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def distance_squared_to(self, other):
        """Optimized distance calculation without sqrt for comparisons"""
        return (self.x - other.x)**2 + (self.y - other.y)**2
    
    def update(self):
        # Smooth movement
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1
        
        # Update transition for color blending
        if self.transition < 1:
            self.transition = min(1, self.transition + 0.05)
        
        # Pulse effect when cluster changes
        if self.scale > 1.0:
            self.scale -= 0.05
        
        # Update trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

class Centroid:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.color = color
        self.pulse = 0
        self.glow_radius = 0
    
    def update(self):
        # Smooth movement animation
        self.x += (self.target_x - self.x) * 0.08
        self.y += (self.target_y - self.y) * 0.08
        
        # Pulsing animation
        self.pulse += 0.1
        self.glow_radius = 20 + math.sin(self.pulse) * 5

class ParticleEffect:
    def __init__(self, x, y, color):
        self.particles = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'color': color
            })
    
    def update(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.95
            p['vy'] *= 0.95
            p['life'] -= 0.03
        
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def draw(self, screen):
        for p in self.particles:
            alpha = int(p['life'] * 255)
            color = (*p['color'], alpha)
            size = int(p['life'] * 4)
            pos = (int(p['x']), int(p['y']))
            
            # Create temporary surface for alpha
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            screen.blit(s, (pos[0]-size, pos[1]-size))

class KMeansGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Clustering Visualizer (K-Means / K-Medoids)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)
        self.menu_title_font = pygame.font.Font(None, 54)
        self.menu_section_font = pygame.font.Font(None, 30)
        self.menu_item_font = pygame.font.Font(None, 26)
        self.menu_hint_font = pygame.font.Font(None, 22)

        # Scene system
        # - "menu": main menu (choose algorithm/dataset/K/points)
        # - "game": interactive clustering
        self.scene = "menu"
        
        self.points = []
        self.centroids = []
        self.particles = []
        self.k = 3
        self.running = True
        self.auto_iterate = False
        self.iteration_count = 0
        self.converged = False
        self.show_debug = True
        self.fps = 60
        
        # Input field for point count
        self.input_active = False
        self.input_text = ""
        self.input_field = "points"  # "points" or "k"
        
        # Performance optimization: timer for auto-iteration
        self.last_iteration_time = 0
        # Slightly slower by default so clustering feels more “game-like”
        self.iteration_delay = 300  # milliseconds between iterations
        
        # Point spacing (makes convergence take longer visually + reduces overlap)
        self.min_point_distance = 25
        self.max_tries_per_point = 250
        
        # Data mining features
        self.inertia_history = []  # Track inertia over iterations
        self.show_stats = False  # Toggle advanced stats panel
        self.show_graph = False  # Toggle convergence graph
        self.show_elbow = False  # Toggle elbow method view
        self.dataset_type = "random"  # Current dataset type
        self.elbow_data = []  # Store elbow method results

        # Visual / analysis overlays
        self.show_voronoi = False
        self.voronoi_cell_size = 12  # bigger = faster, smaller = smoother
        self._voronoi_cache_a = {"key": None, "surface": None}
        self._voronoi_cache_b = {"key": None, "surface": None}

        # Algorithm selection
        self.algorithm = "kmeans"  # "kmeans" or "kmedoids"
        self.algorithm_b = "kmedoids" if self.algorithm == "kmeans" else "kmeans"

        # Battle mode (A/B)
        self.battle_mode = False
        self.points_b = []
        self.centroids_b = []
        self.particles_b = []
        self.iteration_count_b = 0
        self.converged_b = False
        self.inertia_history_b = []

        # K-Medoids settings (keep it interactive; exact PAM can be heavy for 500 pts)
        self.kmedoids_candidate_limit = 25  # sample candidates per cluster when large

        # Main menu state
        self.menu_index = 0
        self.menu_algorithm = self.algorithm
        self.menu_dataset = "random"  # random/blobs/moons/circles/csv
        self.menu_points = 50
        self.menu_k = self.k
        self.menu_start_mode = "single"  # single/battle
        self.menu_voronoi = False
        self.menu_message = ""
        self.menu_message_until = 0
        self._menu_preview_cache_key = None
        self._menu_preview_xy = []
        self._menu_layout_cache = None

        # CSV dataset buffer (loaded points)
        self.csv_points = []  # list[(x, y)]
        
        # Generate random points
        self.generate_points(50)
        self.reset_algorithm()

    def _sync_menu_from_game(self):
        self.menu_algorithm = self.algorithm
        self.menu_points = len(self.points) if self.points else 50
        self.menu_k = self.k
        self.menu_dataset = self.dataset_type if self.dataset_type else "random"
        self.menu_start_mode = "battle" if self.battle_mode else "single"
        self.menu_voronoi = bool(self.show_voronoi)
        if self.menu_dataset == "csv":
            # Keep last imported/used CSV points so menu can start with them again
            self.csv_points = [(p.x, p.y) for p in self.points]
        self._regen_menu_preview()

    def _apply_menu_settings_and_start(self):
        self.algorithm = self.menu_algorithm
        self.algorithm_b = "kmedoids" if self.algorithm == "kmeans" else "kmeans"
        self.k = self.menu_k
        self.show_voronoi = bool(self.menu_voronoi)
        self.battle_mode = (self.menu_start_mode == "battle")

        # Generate dataset using chosen point count
        n = int(self.menu_points)
        if self.menu_dataset == "csv" and self.csv_points:
            # Use imported CSV points (sample if needed)
            xy = list(self.csv_points)
            if n <= 0:
                n = len(xy)
            n = min(n, len(xy))
            if len(xy) > n:
                xy = random.sample(xy, n)
            self._set_points_from_xy_list(xy)
            self.dataset_type = "csv"
        elif self.menu_dataset == "blobs":
            self.generate_blobs(n)
        elif self.menu_dataset == "moons":
            self.generate_moons(n)
        elif self.menu_dataset == "circles":
            self.generate_circles(n)
        else:
            self.generate_points(n)

        # Reset algorithm state + assignments (battle mode uses both sides)
        self._invalidate_voronoi_cache()
        self.reset_algorithm()

        # Reset UI toggles for a clean start
        self.auto_iterate = False
        self.show_elbow = False
        self.elbow_data = []

        self.scene = "game"

    def _set_points_from_xy_list(self, xy_list):
        """Replace current points with a list of (x, y) pairs."""
        self.points = []
        for x, y in xy_list:
            self.points.append(Point(float(x), float(y)))

    def _project_root(self):
        # This file lives in Scripts/, so project root is one directory up.
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _ask_open_csv_path(self):
        """Try to open a native file picker to select a CSV file."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Open CSV (x,y)",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=self._project_root(),
            )
            root.destroy()
            return path if path else None
        except Exception:
            return None

    def _ask_save_csv_path(self, default_name="points_export.csv"):
        """Try to open a native file picker to choose an export path."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.asksaveasfilename(
                title="Save CSV",
                defaultextension=".csv",
                initialfile=default_name,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=self._project_root(),
            )
            root.destroy()
            return path if path else None
        except Exception:
            return None

    def import_points_from_csv(self, path=None, stay_in_menu=False):
        """Import points from a CSV file with columns: x,y (header optional)."""
        if path is None:
            path = self._ask_open_csv_path()
        if not path:
            return False

        xy = []
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                try:
                    x = float(row[0])
                    y = float(row[1])
                except ValueError:
                    # Skip header / non-numeric lines
                    continue
                xy.append((x, y))

        if not xy:
            return False

        self.csv_points = xy
        self.menu_dataset = "csv"
        self.menu_points = len(xy)
        self._regen_menu_preview()

        if not stay_in_menu:
            self._set_points_from_xy_list(xy)
            self.dataset_type = "csv"
            self._invalidate_voronoi_cache()
            self.reset_algorithm()
        return True

    def export_points_to_csv(self, path=None):
        """Export current points (and cluster labels) to a CSV file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"clustering_export_{timestamp}.csv"

        if path is None:
            path = self._ask_save_csv_path(default_name=default_name)
        if not path:
            # Fallback: save into project root
            path = os.path.join(self._project_root(), default_name)

        if self.battle_mode and self.points_b:
            header = ["x", "y", "cluster_a", "cluster_b"]
            rows = []
            for pa, pb in zip(self.points, self.points_b):
                rows.append([pa.x, pa.y, pa.cluster, pb.cluster])
        else:
            header = ["x", "y", "cluster"]
            rows = []
            for p in self.points:
                rows.append([p.x, p.y, p.cluster])

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        return True

    def _set_menu_message(self, text, duration_ms=2500):
        self.menu_message = text
        self.menu_message_until = pygame.time.get_ticks() + int(duration_ms)

    def _menu_dataset_label(self):
        if self.menu_dataset == "csv":
            return "CSV (loaded)" if self.csv_points else "CSV (none)"
        return self.menu_dataset.capitalize()

    def _menu_get_items(self):
        """Declarative menu definition for rendering + input."""
        return [
            {
                "key": "algorithm",
                "label": "Algorithm",
                "type": "choice",
                "value": self.menu_algorithm,
                "choices": [("kmeans", "K-Means"), ("kmedoids", "K-Medoids")],
                "hint": "Choose the clustering algorithm.",
            },
            {
                "key": "start_mode",
                "label": "Mode",
                "type": "choice",
                "value": self.menu_start_mode,
                "choices": [("single", "Single"), ("battle", "Battle (A/B)")],
                "hint": "Battle mode compares two algorithms side-by-side.",
            },
            {
                "key": "dataset",
                "label": "Dataset",
                "type": "choice",
                "value": self.menu_dataset,
                "choices": [
                    ("random", "Random"),
                    ("blobs", "Blobs"),
                    ("moons", "Moons"),
                    ("circles", "Circles"),
                    ("csv", "CSV"),
                ],
                "hint": "Pick a synthetic dataset or load from CSV (x,y).",
            },
            {
                "key": "points",
                "label": "Points (N)",
                "type": "int",
                "value": int(self.menu_points),
                "min": 1,
                "max": 500,
                "step": 10,
                "hint": "Number of points to generate/use.",
            },
            {
                "key": "k",
                "label": "Clusters (K)",
                "type": "int",
                "value": int(self.menu_k),
                "min": 1,
                "max": 10,
                "step": 1,
                "hint": "Number of clusters.",
            },
            {
                "key": "voronoi",
                "label": "Voronoi Regions",
                "type": "bool",
                "value": bool(self.menu_voronoi),
                "hint": "Show decision regions (nearest centroid/medoid).",
            },
            {"key": "start", "label": "Start", "type": "action", "hint": "Start the simulation."},
            {"key": "import", "label": "Import CSV", "type": "action", "hint": "Load a CSV file with x,y columns."},
            {"key": "export", "label": "Export CSV", "type": "action", "hint": "Export current points (and labels if available)."},
            {"key": "quit", "label": "Quit", "type": "action", "hint": "Exit the program."},
        ]

    def _menu_apply_item_value(self, item_key, new_value):
        """Apply changes coming from menu controls."""
        if item_key == "algorithm":
            self.menu_algorithm = new_value
        elif item_key == "start_mode":
            self.menu_start_mode = new_value
        elif item_key == "dataset":
            self.menu_dataset = new_value
            if new_value == "csv" and not self.csv_points:
                self._set_menu_message("No CSV loaded. Press I or choose Import CSV.")
        elif item_key == "points":
            self.menu_points = int(new_value)
        elif item_key == "k":
            self.menu_k = int(new_value)
        elif item_key == "voronoi":
            self.menu_voronoi = bool(new_value)
        self._regen_menu_preview()

    def _regen_menu_preview(self):
        """Generate/caches a small preview dataset for the menu right panel."""
        key = (self.menu_dataset, int(self.menu_points), int(self.menu_k), len(self.csv_points))
        if self._menu_preview_cache_key == key:
            return
        self._menu_preview_cache_key = key

        # Keep preview light
        n = min(220, max(30, int(self.menu_points)))
        k = max(1, min(10, int(self.menu_k)))

        def clamp_xy(x, y):
            x = max(SIDE_MARGIN, min(WIDTH - SIDE_MARGIN, x))
            y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
            return x, y

        xy = []
        if self.menu_dataset == "csv":
            if self.csv_points:
                xy = list(self.csv_points)
                if len(xy) > n:
                    xy = random.sample(xy, n)
            else:
                xy = []
        elif self.menu_dataset == "moons":
            half = n // 2
            for _ in range(half):
                angle = random.uniform(0, math.pi)
                radius = random.uniform(60, 100)
                x = WIDTH // 2 - 150 + radius * math.cos(angle)
                y = HEIGHT // 2 - 100 + radius * math.sin(angle)
                xy.append(clamp_xy(x, y))
            for _ in range(n - half):
                angle = random.uniform(math.pi, 2 * math.pi)
                radius = random.uniform(60, 100)
                x = WIDTH // 2 + 150 + radius * math.cos(angle)
                y = HEIGHT // 2 + 50 + radius * math.sin(angle)
                xy.append(clamp_xy(x, y))
        elif self.menu_dataset == "circles":
            cx, cy = WIDTH // 2, HEIGHT // 2 - 60
            inner = n // 3
            for _ in range(inner):
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(30, 70)
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                xy.append(clamp_xy(x, y))
            for _ in range(n - inner):
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(120, 180)
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                xy.append(clamp_xy(x, y))
        elif self.menu_dataset == "blobs":
            centers = min(max(2, k), 5)
            per = max(1, n // centers)
            margin = 100
            blob_centers = []
            for _ in range(centers):
                blob_centers.append((
                    random.randint(margin + 150, WIDTH - margin - 150),
                    random.randint(margin + 100, HEIGHT - margin - 200),
                ))
            for i in range(centers):
                bx, by = blob_centers[i]
                for _ in range(per):
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.gauss(0, 40)
                    x = bx + radius * math.cos(angle)
                    y = by + radius * math.sin(angle)
                    x = max(margin, min(WIDTH - margin, x))
                    y = max(margin, min(HEIGHT - margin - 120, y))
                    xy.append((x, y))
            while len(xy) < n:
                xy.append((random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN), random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)))
        else:
            # Random (simple uniform preview; keep it fast)
            for _ in range(n):
                xy.append((random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN), random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)))

        self._menu_preview_xy = xy
    
    def _generate_spaced_points(self, n, min_dist=25, max_tries_per_point=200):
        """Generate points with a minimum distance between them."""
        self.points = []
        min_dist_sq = min_dist * min_dist
        
        for _ in range(n):
            placed = False
            for _try in range(max_tries_per_point):
                x = random.randint(80, WIDTH - 80)
                y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
                
                ok = True
                for p in self.points:
                    dx = p.x - x
                    dy = p.y - y
                    if dx * dx + dy * dy < min_dist_sq:
                        ok = False
                        break
                
                if ok:
                    self.points.append(Point(x, y))
                    placed = True
                    break
            
            # Fallback (if screen gets too dense for the requested min_dist)
            if not placed:
                x = random.randint(80, WIDTH - 80)
                y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
                self.points.append(Point(x, y))
    
    def generate_points(self, n):
        """Generate random points (spaced out)."""
        self._generate_spaced_points(
            n,
            min_dist=self.min_point_distance,
            max_tries_per_point=self.max_tries_per_point,
        )
        self.dataset_type = "random"
    
    def generate_blobs(self, n, centers=None):
        """Generate well-separated blob clusters"""
        if centers is None:
            centers = self.k
        
        self.points = []
        points_per_cluster = n // centers
        margin = 100
        
        for i in range(centers):
            # Center of each blob
            center_x = random.randint(margin + 150, WIDTH - margin - 150)
            center_y = random.randint(margin + 100, HEIGHT - margin - 200)
            
            # Generate points around center with Gaussian-like distribution
            for _ in range(points_per_cluster):
                angle = random.uniform(0, 2 * math.pi)
                radius = random.gauss(0, 40)  # Standard deviation of 40
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # Clamp to screen bounds
                x = max(margin, min(WIDTH - margin, x))
                y = max(margin, min(HEIGHT - margin - 120, y))
                
                self.points.append(Point(x, y))
        
        # Add remaining points randomly
        for _ in range(n - (points_per_cluster * centers)):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
            self.points.append(Point(x, y))
        
        self.dataset_type = "blobs"
    
    def generate_moons(self, n):
        """Generate two moon-shaped clusters"""
        self.points = []
        half = n // 2
        
        # First moon (upper)
        for i in range(half):
            angle = random.uniform(0, math.pi)
            radius = random.uniform(60, 100)
            x = WIDTH // 2 - 150 + radius * math.cos(angle)
            y = HEIGHT // 2 - 100 + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
            self.points.append(Point(x, y))
        
        # Second moon (lower)
        for i in range(n - half):
            angle = random.uniform(math.pi, 2 * math.pi)
            radius = random.uniform(60, 100)
            x = WIDTH // 2 + 150 + radius * math.cos(angle)
            y = HEIGHT // 2 + 50 + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
            self.points.append(Point(x, y))
        
        self.dataset_type = "moons"
    
    def generate_circles(self, n):
        """Generate concentric circle clusters"""
        self.points = []
        center_x, center_y = WIDTH // 2, HEIGHT // 2 - 60
        
        # Inner circle
        for i in range(n // 3):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(30, 70)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
            self.points.append(Point(x, y))
        
        # Outer circle
        for i in range(n - n // 3):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(120, 180)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
            self.points.append(Point(x, y))
        
        self.dataset_type = "circles"
    
    def reset_centroids(self):
        self.centroids = []
        for i in range(self.k):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
            self.centroids.append(Centroid(x, y, COLORS[i % len(COLORS)]))
        self.iteration_count = 0
        self.converged = False
        self.inertia_history = []  # Reset inertia history

    def reset_medoids(self):
        """Initialize medoids by selecting real points as representatives."""
        if not self.points:
            self.reset_centroids()
            return

        chosen = random.sample(self.points, k=min(self.k, len(self.points)))
        self.centroids = []
        for i in range(self.k):
            p = chosen[i % len(chosen)]
            self.centroids.append(Centroid(p.x, p.y, COLORS[i % len(COLORS)]))

        self.iteration_count = 0
        self.converged = False
        self.inertia_history = []

    def reset_algorithm(self):
        """Reset the currently selected algorithm state (centroids/medoids + counters)."""
        # Any reset changes decision regions
        self._invalidate_voronoi_cache()

        if self.battle_mode:
            # Keep battle comparable: clone points for B and initialize both sides together.
            self.algorithm_b = "kmedoids" if self.algorithm == "kmeans" else "kmeans"
            self.points_b = self._clone_points(self.points)
            self.particles_b = []
            self._reset_battle_shared_init()
            return

        if self.algorithm == "kmedoids":
            self.reset_medoids()
        else:
            self.reset_centroids()

        # Reset point assignments
        for point in self.points:
            point.cluster = None
            point.prev_cluster = None

    def enable_battle_mode(self):
        """Enable A/B battle mode (A uses selected algorithm, B uses the other)."""
        self.battle_mode = True
        # Battle mode draws a scaled view; particles are disabled for clarity/perf
        self.particles = []
        self.particles_b = []
        self.reset_algorithm()

    def disable_battle_mode(self):
        """Disable A/B battle mode and return to single-view mode."""
        self.battle_mode = False
        self.points_b = []
        self.centroids_b = []
        self.particles_b = []
        self.iteration_count_b = 0
        self.converged_b = False
        self.inertia_history_b = []
        self._invalidate_voronoi_cache()

    def _reset_battle_shared_init(self):
        """Initialize both models with shared seeds for fair comparison."""
        self.particles = []
        self.particles_b = []

        if not self.points:
            self.centroids = []
            self.centroids_b = []
            return

        seeds = random.sample(self.points, k=min(self.k, len(self.points)))
        self.centroids = []
        self.centroids_b = []
        for i in range(self.k):
            p = seeds[i % len(seeds)]
            color = COLORS[i % len(COLORS)]
            self.centroids.append(Centroid(p.x, p.y, color))
            self.centroids_b.append(Centroid(p.x, p.y, color))

        # Reset state for both sides
        self.iteration_count = 0
        self.converged = False
        self.inertia_history = []

        self.iteration_count_b = 0
        self.converged_b = False
        self.inertia_history_b = []

        for p in self.points:
            p.cluster = None
            p.prev_cluster = None
        for p in self.points_b:
            p.cluster = None
            p.prev_cluster = None

    def _step_model(self, points, centroids, algorithm, inertia_history):
        """Run one iteration of a model and record inertia. Returns no_changes."""
        no_changes = self._assign_clusters_for(points, centroids, particles=None, max_particles_per_step=0)
        if algorithm == "kmedoids":
            self._update_medoids_for(points, centroids)
        else:
            self._update_centroids_for(points, centroids)

        inertia = self._calculate_inertia_for(points, centroids)
        inertia_history.append(inertia)
        if len(inertia_history) > 100:
            inertia_history.pop(0)

        return no_changes

    def step_battle(self):
        """Advance both A and B models by one iteration (if not converged)."""
        # A model
        if not self.converged:
            no_changes_a = self._step_model(self.points, self.centroids, self.algorithm, self.inertia_history)
            self.iteration_count += 1
            if no_changes_a:
                self.converged = True

        # B model
        if self.points_b and self.centroids_b and not self.converged_b:
            no_changes_b = self._step_model(self.points_b, self.centroids_b, self.algorithm_b, self.inertia_history_b)
            self.iteration_count_b += 1
            if no_changes_b:
                self.converged_b = True

    def step_algorithm(self):
        """Run one step of the currently selected algorithm."""
        if self.battle_mode:
            self.step_battle()
            return
        if self.algorithm == "kmedoids":
            self.kmedoids_step()
        else:
            self.kmeans_step()

    def _invalidate_voronoi_cache(self):
        self._voronoi_cache_a["key"] = None
        self._voronoi_cache_a["surface"] = None
        self._voronoi_cache_b["key"] = None
        self._voronoi_cache_b["surface"] = None

    def _clone_points(self, points):
        return [Point(p.x, p.y) for p in points]

    def _assign_clusters_for(self, points, centroids, particles=None, max_particles_per_step=0):
        """Assign each point to nearest centroid (generic)."""
        changes = 0
        particle_count = 0

        for point in points:
            prev_cluster = point.cluster
            min_dist_sq = float('inf')
            closest_centroid = 0

            for i, centroid in enumerate(centroids):
                dist_sq = point.distance_squared_to(centroid)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_centroid = i

            if point.cluster != closest_centroid:
                changes += 1
                point.prev_cluster = point.cluster
                point.cluster = closest_centroid
                point.transition = 0
                point.scale = 1.5

                if (
                    particles is not None
                    and point.prev_cluster is not None
                    and particle_count < max_particles_per_step
                ):
                    particles.append(ParticleEffect(point.x, point.y, centroids[point.cluster].color))
                    particle_count += 1

        return changes == 0

    def _update_centroids_for(self, points, centroids):
        """Move centroids to mean of their clusters (generic)."""
        for i, centroid in enumerate(centroids):
            cluster_points = [p for p in points if p.cluster == i]
            if cluster_points:
                mean_x = sum(p.x for p in cluster_points) / len(cluster_points)
                mean_y = sum(p.y for p in cluster_points) / len(cluster_points)
                centroid.x = mean_x
                centroid.y = mean_y
                centroid.target_x = mean_x
                centroid.target_y = mean_y

    def _calculate_inertia_for(self, points, centroids):
        """Calculate WCSS / Inertia for a given clustering state."""
        total = 0
        for point in points:
            if point.cluster is not None:
                centroid = centroids[point.cluster]
                total += point.distance_squared_to(centroid)
        return total

    def _update_medoids_for(self, points, centroids):
        """Update medoids (approximate PAM) for a given clustering state."""
        if not points:
            return

        for i, centroid in enumerate(centroids):
            cluster_points = [p for p in points if p.cluster == i]
            if not cluster_points:
                p = random.choice(points)
                centroid.x = p.x
                centroid.y = p.y
                centroid.target_x = p.x
                centroid.target_y = p.y
                continue

            if len(cluster_points) <= self.kmedoids_candidate_limit:
                candidates = cluster_points
            else:
                candidates = random.sample(cluster_points, self.kmedoids_candidate_limit)

            best_point = None
            best_cost = float("inf")

            for candidate in candidates:
                cx, cy = candidate.x, candidate.y
                cost = 0
                for p in cluster_points:
                    dx = p.x - cx
                    dy = p.y - cy
                    cost += dx * dx + dy * dy

                if cost < best_cost:
                    best_cost = cost
                    best_point = candidate

            if best_point is not None:
                centroid.x = best_point.x
                centroid.y = best_point.y
                centroid.target_x = best_point.x
                centroid.target_y = best_point.y
    
    def assign_clusters(self):
        """Assign each point to nearest centroid"""
        return self._assign_clusters_for(self.points, self.centroids, particles=self.particles, max_particles_per_step=10)
    
    def update_centroids(self):
        """Move centroids to mean of their clusters"""
        self._update_centroids_for(self.points, self.centroids)
    
    def calculate_inertia(self):
        """Calculate Within-Cluster Sum of Squares (WCSS) / Inertia"""
        return self._calculate_inertia_for(self.points, self.centroids)
    
    def kmeans_step(self):
        """One iteration of K-Means"""
        if not self.converged:
            no_changes = self.assign_clusters()
            self.update_centroids()
            self.iteration_count += 1
            
            # Track inertia for convergence graph
            inertia = self.calculate_inertia()
            self.inertia_history.append(inertia)
            
            # Keep only last 100 iterations for graph
            if len(self.inertia_history) > 100:
                self.inertia_history.pop(0)
            
            if no_changes:
                self.converged = True

    def update_medoids(self):
        """Update medoids (approximate PAM): pick the point minimizing total intra-cluster distance."""
        self._update_medoids_for(self.points, self.centroids)

    def kmedoids_step(self):
        """One iteration of K-Medoids."""
        if not self.centroids:
            self.reset_medoids()

        if not self.converged:
            no_changes = self.assign_clusters()
            self.update_medoids()
            self.iteration_count += 1

            inertia = self.calculate_inertia()
            self.inertia_history.append(inertia)
            if len(self.inertia_history) > 100:
                self.inertia_history.pop(0)

            if no_changes:
                self.converged = True
    
    def draw_glow(self, pos, color, radius):
        """Draw a glowing circle effect (optimized)"""
        # Only draw glow if radius is reasonable
        if radius > 0:
            max_radius = int(radius * 3)
            s = pygame.Surface((max_radius*2, max_radius*2), pygame.SRCALPHA)
            for i in range(3, 0, -1):
                alpha = 40 * i
                glow_color = (*color, alpha)
                r = int(radius * i)
                pygame.draw.circle(s, glow_color, (max_radius, max_radius), r)
            self.screen.blit(s, (pos[0]-max_radius, pos[1]-max_radius))
    
    def lerp_color(self, c1, c2, t):
        """Linear interpolation between two colors"""
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def _get_voronoi_surface(self, centroids, cache, view_w, view_h, x_scale=1.0):
        """Return a cached Voronoi/decision-region surface for the given centroids."""
        if not centroids or view_w <= 0 or view_h <= 0:
            return None

        cell = max(4, int(self.voronoi_cell_size))
        centroid_key = tuple((int(c.x), int(c.y), idx) for idx, c in enumerate(centroids))
        key = (view_w, view_h, cell, round(x_scale, 3), centroid_key)

        if cache["key"] == key and cache["surface"] is not None:
            return cache["surface"]

        s = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        alpha = 45

        for y in range(0, view_h, cell):
            for x in range(0, view_w, cell):
                # Convert view coordinates back to model coordinates for distance checks
                mx = x / x_scale if x_scale != 0 else x
                my = y

                best_i = 0
                best_d = float("inf")
                for i, c in enumerate(centroids):
                    dx = c.x - mx
                    dy = c.y - my
                    d = dx * dx + dy * dy
                    if d < best_d:
                        best_d = d
                        best_i = i

                color = centroids[best_i].color
                pygame.draw.rect(s, (*color, alpha), (x, y, cell, cell))

        cache["key"] = key
        cache["surface"] = s
        return s

    def _draw_model_view(self, points, centroids, offset_x, x_scale, view_w, view_h, draw_particles=False, title=None):
        """Draw one clustering state into a viewport (used for battle mode)."""
        # Voronoi background (only over the main area, not the bottom UI)
        if self.show_voronoi:
            cache = self._voronoi_cache_a if offset_x == 0 else self._voronoi_cache_b
            v = self._get_voronoi_surface(centroids, cache, view_w, view_h, x_scale=x_scale)
            if v is not None:
                self.screen.blit(v, (offset_x, 0))

        # Connection lines
        connection_surface = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        for p in points:
            if p.cluster is not None and 0 <= p.y < view_h:
                c = centroids[p.cluster]
                color = (*c.color, 30)
                pygame.draw.line(
                    connection_surface,
                    color,
                    (int(p.x * x_scale), int(p.y)),
                    (int(c.x * x_scale), int(c.y)),
                    1,
                )
        self.screen.blit(connection_surface, (offset_x, 0))

        # Centroid glows
        for c in centroids:
            self.draw_glow((offset_x + int(c.x * x_scale), int(c.y)), c.color, int(c.glow_radius))

        # Trails
        trail_surface = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        for p in points:
            if len(p.trail) > 1 and p.cluster is not None:
                color = centroids[p.cluster].color
                for i in range(len(p.trail) - 1):
                    alpha = int((i / len(p.trail)) * 100)
                    trail_color = (*color, alpha)
                    x1, y1 = p.trail[i]
                    x2, y2 = p.trail[i + 1]
                    pygame.draw.line(
                        trail_surface,
                        trail_color,
                        (x1 * x_scale, y1),
                        (x2 * x_scale, y2),
                        2,
                    )
        self.screen.blit(trail_surface, (offset_x, 0))

        # Points
        for p in points:
            if p.cluster is None:
                continue
            if p.prev_cluster is not None and p.transition < 1:
                old_color = centroids[p.prev_cluster].color
                new_color = centroids[p.cluster].color
                color = self.lerp_color(old_color, new_color, p.transition)
            else:
                color = centroids[p.cluster].color

            size = int(6 * p.scale)
            pygame.draw.circle(self.screen, color, (offset_x + int(p.x * x_scale), int(p.y)), size)
            pygame.draw.circle(self.screen, WHITE, (offset_x + int(p.x * x_scale), int(p.y)), size, 1)

        # Centroids
        for c in centroids:
            pos = (offset_x + int(c.x * x_scale), int(c.y))
            pygame.draw.circle(self.screen, WHITE, pos, 16)
            pygame.draw.circle(self.screen, c.color, pos, 14)
            pygame.draw.circle(self.screen, WHITE, pos, 14, 2)

        # Optional particles (single-view only)
        if draw_particles:
            for particle in self.particles:
                particle.draw(self.screen)

        if title:
            t = self.small_font.render(title, True, TEXT_COLOR)
            self.screen.blit(t, (offset_x + 10, 10))

    def draw_battle_view(self):
        """Draw split-screen comparison between algorithm A and B."""
        view_h = HEIGHT - UI_PANEL_HEIGHT
        half = WIDTH // 2
        x_scale = 0.5

        title_a = f"A: {'K-Means' if self.algorithm == 'kmeans' else 'K-Medoids'}  (iter {self.iteration_count})"
        title_b = f"B: {'K-Means' if self.algorithm_b == 'kmeans' else 'K-Medoids'}  (iter {self.iteration_count_b})"

        self._draw_model_view(self.points, self.centroids, 0, x_scale, half, view_h, draw_particles=False, title=title_a)
        self._draw_model_view(self.points_b, self.centroids_b, half, x_scale, half, view_h, draw_particles=False, title=title_b)

        # Divider
        pygame.draw.line(self.screen, (80, 80, 110), (half, 0), (half, view_h), 2)
    
    def draw(self):
        if self.scene == "menu":
            self.draw_main_menu()
            pygame.display.flip()
            return

        self.screen.fill(BG_COLOR)

        # Main scene rendering
        if self.battle_mode:
            self.draw_battle_view()
        else:
            # Voronoi / decision regions (cached)
            if self.show_voronoi:
                view_h = HEIGHT - UI_PANEL_HEIGHT
                v = self._get_voronoi_surface(self.centroids, self._voronoi_cache_a, WIDTH, view_h, x_scale=1.0)
                if v is not None:
                    self.screen.blit(v, (0, 0))
        
            # Optimized: Use single surface for all connection lines
            connection_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for point in self.points:
                if point.cluster is not None:
                    centroid = self.centroids[point.cluster]
                    color = (*centroid.color, 30)
                    pygame.draw.line(connection_surface, color, (int(point.x), int(point.y)), 
                                   (int(centroid.x), int(centroid.y)), 1)
            self.screen.blit(connection_surface, (0, 0))
            
            # Draw centroid glows
            for centroid in self.centroids:
                self.draw_glow((int(centroid.x), int(centroid.y)), 
                              centroid.color, int(centroid.glow_radius))
            
            # Optimized: Use single surface for all trails
            trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for point in self.points:
                if len(point.trail) > 1 and point.cluster is not None:
                    color = self.centroids[point.cluster].color
                    for i in range(len(point.trail) - 1):
                        alpha = int((i / len(point.trail)) * 100)
                        trail_color = (*color, alpha)
                        pygame.draw.line(trail_surface, trail_color, point.trail[i], point.trail[i+1], 2)
            self.screen.blit(trail_surface, (0, 0))
            
            # Draw points with color transitions
            for point in self.points:
                if point.cluster is not None:
                    if point.prev_cluster is not None and point.transition < 1:
                        # Blend colors during transition
                        old_color = self.centroids[point.prev_cluster].color
                        new_color = self.centroids[point.cluster].color
                        color = self.lerp_color(old_color, new_color, point.transition)
                    else:
                        color = self.centroids[point.cluster].color
                    
                    size = int(6 * point.scale)
                    pygame.draw.circle(self.screen, color, (int(point.x), int(point.y)), size)
                    # Add white highlight
                    pygame.draw.circle(self.screen, WHITE, (int(point.x), int(point.y)), size, 1)
            
            # Draw centroids
            for centroid in self.centroids:
                pos = (int(centroid.x), int(centroid.y))
                pygame.draw.circle(self.screen, WHITE, pos, 16)
                pygame.draw.circle(self.screen, centroid.color, pos, 14)
                pygame.draw.circle(self.screen, WHITE, pos, 14, 2)
            
            # Draw particle effects
            for particle in self.particles:
                particle.draw(self.screen)
        
        # Draw convergence graph
        if self.show_graph:
            self.draw_convergence_graph()
        
        # Draw elbow method visualizer
        if self.show_elbow:
            self.draw_elbow_method()

        # Draw debug panel (top-right)
        if self.show_debug:
            self.draw_debug_panel()
        
        # Draw stats panel (if enabled)
        if self.show_stats:
            self.draw_stats_panel()
        
        # Draw main UI panel
        panel_rect = pygame.Rect(0, HEIGHT - UI_PANEL_HEIGHT, WIDTH, UI_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLORS[0], panel_rect, 2)
        
        # Draw status
        status_text = "CONVERGED ✓" if self.converged else ("AUTO" if self.auto_iterate else "PAUSED")
        status_color = COLORS[1] if self.converged else (COLORS[2] if self.auto_iterate else TEXT_COLOR)
        status = self.font.render(status_text, True, status_color)
        self.screen.blit(status, (WIDTH - 220, HEIGHT - UI_PANEL_HEIGHT + 20))
        
        # Draw controls
        controls = [
            "SPACE: Step  |  A: Auto  |  R: Reset  |  D: Debug  |  C: Clear",
            f"M: Menu  |  5/6: Algo  |  B: Battle  |  V: Voronoi  |  I/O: CSV  |  IterA: {self.iteration_count}" + (f"  IterB: {self.iteration_count_b}" if self.battle_mode else ""),
            "1: Blobs  |  2: Moons  |  3: Circles  |  4: Random  |  S: Stats  |  G: Graph  |  E: Elbow"
        ]
        
        y_offset = HEIGHT - 100
        for text in controls:
            surface = self.small_font.render(text, True, TEXT_COLOR)
            self.screen.blit(surface, (20, y_offset))
            y_offset += 28
        
        # Draw input dialog if active
        if self.input_active:
            self.draw_input_dialog()
        
        pygame.display.flip()

    def draw_main_menu(self):
        """Main menu scene: choose algorithm/dataset/points/K and start."""
        self.screen.fill(BG_COLOR)

        # Ensure preview is available
        if self._menu_preview_cache_key is None:
            self._regen_menu_preview()

        title = self.menu_title_font.render("Clustering Lab", True, COLORS[1])
        subtitle = self.menu_section_font.render("Choose settings then press ENTER to start", True, TEXT_COLOR)
        self.screen.blit(title, (24, 18))
        self.screen.blit(subtitle, (24, 62))

        items = self._menu_get_items()
        self.menu_index = max(0, min(self.menu_index, len(items) - 1))

        # Layout: left settings panel, right preview panel, bottom help
        top_y = 110
        bottom_h = 120
        content_h = HEIGHT - bottom_h - top_y - 10

        left_w = 420
        left = pygame.Rect(20, top_y, left_w, content_h)
        right = pygame.Rect(left.right + 15, top_y, WIDTH - (left.right + 15) - 20, content_h)

        pygame.draw.rect(self.screen, UI_BG, left, border_radius=14)
        pygame.draw.rect(self.screen, COLORS[3], left, 2, border_radius=14)
        pygame.draw.rect(self.screen, UI_BG, right, border_radius=14)
        pygame.draw.rect(self.screen, COLORS[2], right, 2, border_radius=14)

        # Settings section title
        s_title = self.menu_section_font.render("Settings", True, TEXT_COLOR)
        self.screen.blit(s_title, (left.x + 16, left.y + 12))

        # Render items + remember row rects for mouse
        row_y = left.y + 52
        row_h = 38
        self._menu_layout_cache = {"left": left, "right": right, "rows": []}

        for idx, it in enumerate(items):
            selected = (idx == self.menu_index)
            row_rect = pygame.Rect(left.x + 10, row_y - 4, left.w - 20, row_h)
            self._menu_layout_cache["rows"].append((row_rect, it["key"]))

            if selected:
                pygame.draw.rect(self.screen, (70, 90, 130), row_rect, border_radius=10)
                pygame.draw.rect(self.screen, COLORS[1], row_rect, 2, border_radius=10)

            label = it["label"]
            value_text = ""
            if it["type"] == "choice":
                # Find display label
                for v, disp in it["choices"]:
                    if v == it["value"]:
                        value_text = disp
                        break
            elif it["type"] == "int":
                value_text = str(it["value"])
            elif it["type"] == "bool":
                value_text = "On" if it["value"] else "Off"
            elif it["type"] == "action":
                value_text = "ENTER"

            label_s = self.menu_item_font.render(label, True, TEXT_COLOR if not selected else WHITE)
            value_s = self.menu_item_font.render(value_text, True, COLORS[1] if selected else TEXT_COLOR)
            self.screen.blit(label_s, (row_rect.x + 12, row_rect.y + 8))
            self.screen.blit(value_s, (row_rect.right - value_s.get_width() - 12, row_rect.y + 8))

            row_y += row_h + 6

        # Preview panel
        p_title = self.menu_section_font.render("Preview", True, TEXT_COLOR)
        self.screen.blit(p_title, (right.x + 16, right.y + 12))

        preview_rect = pygame.Rect(right.x + 14, right.y + 50, right.w - 28, right.h - 64)
        pygame.draw.rect(self.screen, (28, 28, 38), preview_rect, border_radius=12)
        pygame.draw.rect(self.screen, (70, 70, 95), preview_rect, 2, border_radius=12)

        # Plot preview points scaled into preview_rect
        if self.menu_dataset == "csv" and not self.csv_points:
            msg = self.menu_item_font.render("No CSV loaded. Press I or select Import CSV.", True, COLORS[0])
            self.screen.blit(msg, (preview_rect.x + 12, preview_rect.y + 12))
        else:
            xy = self._menu_preview_xy
            if xy:
                xs = [p[0] for p in xy]
                ys = [p[1] for p in xy]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                dx = max_x - min_x if max_x != min_x else 1
                dy = max_y - min_y if max_y != min_y else 1

                for x, y in xy:
                    px = preview_rect.x + 10 + int(((x - min_x) / dx) * (preview_rect.w - 20))
                    py = preview_rect.y + 10 + int(((y - min_y) / dy) * (preview_rect.h - 20))
                    pygame.draw.circle(self.screen, (180, 180, 195), (px, py), 2)

        # Bottom help + description
        help_box = pygame.Rect(20, HEIGHT - bottom_h, WIDTH - 40, bottom_h - 10)
        pygame.draw.rect(self.screen, UI_BG, help_box, border_radius=14)
        pygame.draw.rect(self.screen, COLORS[0], help_box, 2, border_radius=14)

        # Description of selected item
        hint = items[self.menu_index].get("hint", "")
        hint_s = self.menu_hint_font.render(hint, True, TEXT_COLOR)
        self.screen.blit(hint_s, (help_box.x + 16, help_box.y + 12))

        # Controls
        line1 = "UP/DOWN: select   LEFT/RIGHT: change   ENTER: activate/start   ESC: quit"
        line2 = "Quick: 1-4 dataset  5/6 algorithm  B battle  V Voronoi  I import CSV  O export CSV"
        self.screen.blit(self.menu_hint_font.render(line1, True, TEXT_COLOR), (help_box.x + 16, help_box.y + 44))
        self.screen.blit(self.menu_hint_font.render(line2, True, TEXT_COLOR), (help_box.x + 16, help_box.y + 70))

        # Status message (toast)
        if self.menu_message and pygame.time.get_ticks() < self.menu_message_until:
            toast = self.menu_hint_font.render(self.menu_message, True, COLORS[1])
            self.screen.blit(toast, (WIDTH - toast.get_width() - 24, 24))
    
    def draw_debug_panel(self):
        """Draw debug information panel"""
        panel_width = 220
        panel_x = WIDTH - panel_width - 10
        panel_y = 10
        
        # Debug info
        debug_info = [
            ("DEBUG INFO", COLORS[3]),
            ("", TEXT_COLOR),
            (f"FPS: {int(self.fps)}", COLORS[1]),
            (f"Points: {len(self.points)}", TEXT_COLOR),
            (f"Clusters (K): {self.k}", TEXT_COLOR),
            (f"Algo: {'K-Means' if self.algorithm == 'kmeans' else 'K-Medoids'}", TEXT_COLOR),
            (f"Iterations: {self.iteration_count}", TEXT_COLOR),
            (f"Particles: {len(self.particles)}", TEXT_COLOR),
            (f"Converged: {'Yes' if self.converged else 'No'}", TEXT_COLOR),
            ("", TEXT_COLOR),
            (f"Inertia: {int(self.calculate_inertia())}", COLORS[1]),
            (f"Dataset: {self.dataset_type}", TEXT_COLOR),
            (f"Voronoi: {'On' if self.show_voronoi else 'Off'}", TEXT_COLOR),
            (f"Battle: {'On' if self.battle_mode else 'Off'}", TEXT_COLOR),
            ("", TEXT_COLOR),
            ("Cluster Sizes:", COLORS[2]),
        ]

        # If battle mode is active, show B model summary above cluster sizes
        if self.battle_mode:
            b_inertia = 0
            if self.points_b and self.centroids_b:
                b_inertia = int(self._calculate_inertia_for(self.points_b, self.centroids_b))
            insert_at = len(debug_info) - 2
            debug_info[insert_at:insert_at] = [
                ("", TEXT_COLOR),
                (f"B Algo: {'K-Means' if self.algorithm_b == 'kmeans' else 'K-Medoids'}", TEXT_COLOR),
                (f"B Iter: {self.iteration_count_b}", TEXT_COLOR),
                (f"B Conv: {'Yes' if self.converged_b else 'No'}", TEXT_COLOR),
                (f"B Inertia: {b_inertia}", COLORS[1]),
            ]
        
        # Add cluster sizes
        for i in range(self.k):
            count = sum(1 for p in self.points if p.cluster == i)
            debug_info.append((f"  Cluster {i+1}: {count}", self.centroids[i].color))
        
        # Calculate dynamic height based on content
        line_height = 18
        padding = 20  # Top and bottom padding
        num_lines = len([item for item in debug_info if item[0]])  # Count non-empty lines
        panel_height = num_lines * line_height + padding
        
        # Ensure minimum height and maximum height (to prevent going off screen)
        panel_height = max(150, min(panel_height, HEIGHT - (UI_PANEL_HEIGHT + 20)))  # Leave space for bottom UI
        
        # Semi-transparent background
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*UI_BG, 230), (0, 0, panel_width, panel_height))
        pygame.draw.rect(s, COLORS[3], (0, 0, panel_width, panel_height), 2)
        self.screen.blit(s, (panel_x, panel_y))
        
        y = panel_y + 10
        for text, color in debug_info:
            if text:
                surface = self.tiny_font.render(text, True, color)
                self.screen.blit(surface, (panel_x + 10, y))
            y += line_height
    
    def draw_input_dialog(self):
        """Draw input dialog for entering values"""
        dialog_width = 400
        dialog_height = 150
        dialog_x = (WIDTH - dialog_width) // 2
        dialog_y = (HEIGHT - dialog_height) // 2
        
        # Background with shadow
        shadow = pygame.Surface((dialog_width + 10, dialog_height + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), (0, 0, dialog_width + 10, dialog_height + 10), border_radius=10)
        self.screen.blit(shadow, (dialog_x - 5, dialog_y - 5))
        
        # Main dialog
        pygame.draw.rect(self.screen, UI_BG, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=8)
        pygame.draw.rect(self.screen, COLORS[2], (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=8)
        
        # Title
        if self.input_field == "points":
            title = "Enter Number of Points"
        else:
            title = "Enter Number of Clusters (K)"
        
        title_surf = self.font.render(title, True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
        self.screen.blit(title_surf, title_rect)
        
        # Input box
        input_box = pygame.Rect(dialog_x + 50, dialog_y + 60, dialog_width - 100, 40)
        pygame.draw.rect(self.screen, BG_COLOR, input_box)
        pygame.draw.rect(self.screen, COLORS[1], input_box, 2)
        
        # Input text
        input_surf = self.font.render(self.input_text + "|", True, TEXT_COLOR)
        self.screen.blit(input_surf, (input_box.x + 10, input_box.y + 8))
        
        # Instructions
        instruction = "Press ENTER to confirm, ESC to cancel"
        instr_surf = self.small_font.render(instruction, True, COLORS[3])
        instr_rect = instr_surf.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 120))
        self.screen.blit(instr_surf, instr_rect)
    
    def draw_convergence_graph_for(self, history, graph_x, graph_y, border_color, line_color, title_text):
        """Draw a graph showing inertia over iterations for a given history."""
        graph_width = 300
        graph_height = 150

        if history is None or len(history) < 2:
            return

        # Background
        s = pygame.Surface((graph_width, graph_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*UI_BG, 240), (0, 0, graph_width, graph_height))
        pygame.draw.rect(s, border_color, (0, 0, graph_width, graph_height), 2)
        self.screen.blit(s, (graph_x, graph_y))

        # Title
        title = self.tiny_font.render(title_text, True, border_color)
        self.screen.blit(title, (graph_x + 5, graph_y + 5))

        max_inertia = max(history)
        min_inertia = min(history)
        range_inertia = max_inertia - min_inertia if max_inertia != min_inertia else 1

        graph_padding = 30
        plot_width = graph_width - graph_padding * 2
        plot_height = graph_height - graph_padding * 2

        points = []
        for i, inertia in enumerate(history):
            x = graph_x + graph_padding + (i / (len(history) - 1)) * plot_width
            normalized = (inertia - min_inertia) / range_inertia
            y = graph_y + graph_padding + plot_height - (normalized * plot_height)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(self.screen, line_color, False, points, 2)

        current = history[-1]
        value_text = self.tiny_font.render(f"Current: {int(current)}", True, line_color)
        self.screen.blit(value_text, (graph_x + 5, graph_y + graph_height - 20))

    def draw_convergence_graph(self):
        """Draw convergence graph(s). In battle mode, draws one per side."""
        if self.battle_mode:
            self.draw_convergence_graph_for(
                self.inertia_history,
                graph_x=10,
                graph_y=40,
                border_color=COLORS[2],
                line_color=COLORS[1],
                title_text="A: Inertia",
            )
            self.draw_convergence_graph_for(
                self.inertia_history_b,
                graph_x=WIDTH - 310,
                graph_y=40,
                border_color=COLORS[0],
                line_color=COLORS[1],
                title_text="B: Inertia",
            )
        else:
            self.draw_convergence_graph_for(
                self.inertia_history,
                graph_x=10,
                graph_y=10,
                border_color=COLORS[2],
                line_color=COLORS[1],
                title_text="Convergence Graph (Inertia)",
            )
    
    def draw_elbow_method(self):
        """Draw elbow method visualizer (K vs Inertia)"""
        if not self.elbow_data:
            return
        
        panel_width = 280
        panel_height = 240
        panel_x = WIDTH - panel_width - 10
        panel_y = HEIGHT - panel_height - 130
        
        # Background
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*UI_BG, 240), (0, 0, panel_width, panel_height))
        pygame.draw.rect(s, COLORS[0], (0, 0, panel_width, panel_height), 2)
        self.screen.blit(s, (panel_x, panel_y))
        
        # Title
        title = self.small_font.render("Elbow Method (K vs Inertia)", True, COLORS[0])
        self.screen.blit(title, (panel_x + 10, panel_y + 5))
        
        if len(self.elbow_data) > 1:
            max_inertia = max(d[1] for d in self.elbow_data)
            min_inertia = min(d[1] for d in self.elbow_data)
            range_inertia = max_inertia - min_inertia if max_inertia != min_inertia else 1
            
            graph_padding = 40
            plot_width = panel_width - graph_padding * 2
            plot_height = panel_height - graph_padding * 2
            
            points = []
            for k, inertia in self.elbow_data:
                x = panel_x + graph_padding + ((k - 1) / (len(self.elbow_data) - 1)) * plot_width
                normalized = (inertia - min_inertia) / range_inertia
                y = panel_y + graph_padding + plot_height - (normalized * plot_height)
                points.append((x, y))
            
            # Draw line
            if len(points) > 1:
                pygame.draw.lines(self.screen, COLORS[1], False, points, 2)
            
            # Draw points
            for i, (k, inertia) in enumerate(self.elbow_data):
                if i < len(points):
                    pygame.draw.circle(self.screen, COLORS[1], (int(points[i][0]), int(points[i][1])), 4)
                    k_text = self.tiny_font.render(f"K={k}", True, TEXT_COLOR)
                    self.screen.blit(k_text, (int(points[i][0]) - 10, int(points[i][1]) + 5))
    
    def calculate_cluster_metrics(self):
        """Calculate advanced cluster quality metrics"""
        metrics = {}
        
        for i in range(self.k):
            cluster_points = [p for p in self.points if p.cluster == i]
            if not cluster_points:
                continue
            
            centroid = self.centroids[i]
            
            # Average distance to centroid
            distances = [p.distance_to(centroid) for p in cluster_points]
            avg_dist = sum(distances) / len(distances) if distances else 0
            
            # Variance (compactness)
            variance = sum((d - avg_dist)**2 for d in distances) / len(distances) if distances else 0
            
            metrics[i] = {
                'size': len(cluster_points),
                'avg_distance': avg_dist,
                'variance': variance,
                'compactness': 1.0 / (1.0 + variance)  # Higher is better
            }
        
        return metrics
    
    def draw_stats_panel(self):
        """Draw advanced statistics panel"""
        panel_width = 250
        panel_x = 10
        panel_y = HEIGHT - (UI_PANEL_HEIGHT + 220)
        
        metrics = self.calculate_cluster_metrics()
        inertia = self.calculate_inertia()
        
        # Calculate cluster separation
        min_separation = float('inf')
        for i in range(self.k):
            for j in range(i + 1, self.k):
                dx = self.centroids[i].x - self.centroids[j].x
                dy = self.centroids[i].y - self.centroids[j].y
                dist = math.sqrt(dx * dx + dy * dy)
                min_separation = min(min_separation, dist)
        
        # Count lines needed
        num_lines = 8 + len(metrics) * 3
        panel_height = num_lines * 18 + 20
        
        # Background
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*UI_BG, 240), (0, 0, panel_width, panel_height))
        pygame.draw.rect(s, COLORS[4], (0, 0, panel_width, panel_height), 2)
        self.screen.blit(s, (panel_x, panel_y))
        
        y = panel_y + 10
        
        # Title
        title = self.small_font.render("ADVANCED STATS", True, COLORS[4])
        self.screen.blit(title, (panel_x + 10, y))
        y += 25
        
        # Overall metrics
        stats = [
            (f"Inertia (WCSS): {int(inertia)}", COLORS[1]),
            (f"Min Separation: {int(min_separation) if min_separation != float('inf') else 0}", TEXT_COLOR),
            ("", TEXT_COLOR),
            ("Per-Cluster Metrics:", COLORS[2]),
        ]

        for text, color in stats:
            if text:
                surface = self.tiny_font.render(text, True, color)
                self.screen.blit(surface, (panel_x + 10, y))
            y += 18

        # Cluster-specific metrics
        for i, metric in metrics.items():
            cluster_text = [
                (f"  Cluster {i+1}:", self.centroids[i].color),
                (f"    Size: {metric['size']}", TEXT_COLOR),
                (f"    Avg Dist: {metric['avg_distance']:.1f}", TEXT_COLOR),
                (f"    Compactness: {metric['compactness']:.2f}", TEXT_COLOR),
            ]
            for text, color in cluster_text:
                surface = self.tiny_font.render(text, True, color)
                self.screen.blit(surface, (panel_x + 10, y))
                y += 18

    # draw_algorithm_menu() removed: algorithm selection now lives in the main menu scene.
    
    def run_elbow_method(self):
        """Run elbow method: test K from 1 to 10 and show results"""
        if not self.points:
            return
        
        self.elbow_data = []
        original_k = self.k
        original_iteration = self.iteration_count
        original_converged = self.converged
        original_algorithm = self.algorithm
        
        # Save current point cluster assignments
        original_clusters = [p.cluster for p in self.points]
        
        # Test K from 1 to min(10, number of points)
        max_k = min(10, len(self.points))
        
        # Elbow method runs K-Means (fast + standard). We restore algorithm after.
        self.algorithm = "kmeans"

        for test_k in range(1, max_k + 1):
            self.k = test_k
            self.reset_centroids()
            
            # Reset point clusters
            for point in self.points:
                point.cluster = None
                point.prev_cluster = None
            
            # Run until convergence or max iterations
            max_iterations = 50
            for _ in range(max_iterations):
                if self.converged:
                    break
                self.kmeans_step()
            
            inertia = self.calculate_inertia()
            self.elbow_data.append((test_k, inertia))
        
        # Restore original state
        self.k = original_k
        self.iteration_count = original_iteration
        self.converged = original_converged
        self.algorithm = original_algorithm
        self.reset_algorithm()
        
        # Restore point clusters
        for i, point in enumerate(self.points):
            point.cluster = original_clusters[i] if i < len(original_clusters) else None
        
        self.show_elbow = True
    
    def update(self):
        if self.scene != "game":
            return
        # Update all animations
        for point in self.points:
            point.update()
        
        for centroid in self.centroids:
            centroid.update()
        
        for particle in self.particles:
            particle.update()
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.particles]

        if self.battle_mode:
            for point in self.points_b:
                point.update()
            for centroid in self.centroids_b:
                centroid.update()
            for particle in self.particles_b:
                particle.update()
            self.particles_b = [p for p in self.particles_b if p.particles]
    
    def handle_menu_event(self, event):
        items = self._menu_get_items()
        self.menu_index = max(0, min(self.menu_index, len(items) - 1))

        # Mouse: click to select/activate
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._menu_layout_cache and "rows" in self._menu_layout_cache:
                mx, my = pygame.mouse.get_pos()
                for rect, key in self._menu_layout_cache["rows"]:
                    if rect.collidepoint(mx, my):
                        # Select row
                        for i, it in enumerate(items):
                            if it["key"] == key:
                                self.menu_index = i
                                break
                        # If action, activate immediately
                        if key in ("start", "import", "export", "quit"):
                            event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
                            self.handle_menu_event(event)
                        return
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % len(items)
            return
        if event.key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % len(items)
            return

        # Quick keys (accessible shortcuts)
        if event.key == pygame.K_5:
            self._menu_apply_item_value("algorithm", "kmeans")
            return
        if event.key == pygame.K_6:
            self._menu_apply_item_value("algorithm", "kmedoids")
            return
        if event.key == pygame.K_b:
            self._menu_apply_item_value("start_mode", "battle" if self.menu_start_mode != "battle" else "single")
            return
        if event.key == pygame.K_v:
            self._menu_apply_item_value("voronoi", not self.menu_voronoi)
            return
        if event.key == pygame.K_1:
            self._menu_apply_item_value("dataset", "blobs")
            return
        if event.key == pygame.K_2:
            self._menu_apply_item_value("dataset", "moons")
            return
        if event.key == pygame.K_3:
            self._menu_apply_item_value("dataset", "circles")
            return
        if event.key == pygame.K_4:
            self._menu_apply_item_value("dataset", "random")
            return
        if event.key == pygame.K_i:
            ok = self.import_points_from_csv(stay_in_menu=True)
            if ok:
                self._menu_apply_item_value("dataset", "csv")
                self._set_menu_message("CSV loaded.")
            else:
                self._set_menu_message("CSV import cancelled or invalid.")
            return
        if event.key == pygame.K_o:
            self.export_points_to_csv()
            self._set_menu_message("Exported CSV.")
            return

        current = items[self.menu_index]

        if event.key == pygame.K_RETURN:
            if current["type"] == "action":
                if current["key"] == "start":
                    if self.menu_dataset == "csv" and not self.csv_points:
                        self._set_menu_message("No CSV loaded. Import first (I).")
                        return
                    self._apply_menu_settings_and_start()
                elif current["key"] == "import":
                    ok = self.import_points_from_csv(stay_in_menu=True)
                    if ok:
                        self._menu_apply_item_value("dataset", "csv")
                        self._set_menu_message("CSV loaded.")
                    else:
                        self._set_menu_message("CSV import cancelled or invalid.")
                elif current["key"] == "export":
                    self.export_points_to_csv()
                    self._set_menu_message("Exported CSV.")
                elif current["key"] == "quit":
                    self.running = False
            return

        # LEFT/RIGHT adjust values
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            delta = -1 if event.key == pygame.K_LEFT else 1
            if current["type"] == "choice":
                choices = [c[0] for c in current["choices"]]
                i = choices.index(current["value"]) if current["value"] in choices else 0
                new_val = choices[(i + delta) % len(choices)]
                self._menu_apply_item_value(current["key"], new_val)
            elif current["type"] == "int":
                step = int(current.get("step", 1))
                new_val = int(current["value"]) + (step * delta)
                new_val = max(int(current.get("min", new_val)), min(int(current.get("max", new_val)), new_val))
                self._menu_apply_item_value(current["key"], new_val)
            elif current["type"] == "bool":
                self._menu_apply_item_value(current["key"], not bool(current["value"]))

    def handle_game_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Handle input dialog
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    try:
                        value = int(self.input_text)
                        if self.input_field == "points":
                            if 1 <= value <= 500:
                                self.generate_points(value)
                                self.reset_algorithm()
                        elif self.input_field == "k":
                            if 1 <= value <= 10:
                                self.k = value
                                self.reset_algorithm()
                    except ValueError:
                        pass
                    self.input_active = False
                    self.input_text = ""
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                    self.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode.isdigit() and len(self.input_text) < 4:
                    self.input_text += event.unicode
                return

            # Normal controls
            if event.key == pygame.K_SPACE:
                self.step_algorithm()
            elif event.key == pygame.K_a:
                self.auto_iterate = not self.auto_iterate
            elif event.key == pygame.K_r:
                self.reset_algorithm()
            elif event.key == pygame.K_d:
                self.show_debug = not self.show_debug
            elif event.key == pygame.K_v:
                self.show_voronoi = not self.show_voronoi
                self._invalidate_voronoi_cache()
            elif event.key == pygame.K_b:
                if self.battle_mode:
                    self.disable_battle_mode()
                else:
                    self.enable_battle_mode()
            elif event.key == pygame.K_i:
                # Import CSV and replace current dataset
                self.import_points_from_csv()
            elif event.key == pygame.K_o:
                # Export current state
                self.export_points_to_csv()
            elif event.key == pygame.K_c:
                self.points.clear()
                self.particles.clear()
                self.converged = False
            elif event.key == pygame.K_p:
                self.input_active = True
                self.input_field = "points"
                self.input_text = ""
            elif event.key == pygame.K_k:
                self.input_active = True
                self.input_field = "k"
                self.input_text = ""
            elif event.key == pygame.K_UP:
                self.k = min(10, self.k + 1)
                self.reset_algorithm()
            elif event.key == pygame.K_DOWN:
                self.k = max(1, self.k - 1)
                self.reset_algorithm()
            elif event.key == pygame.K_s:
                self.show_stats = not self.show_stats
            elif event.key == pygame.K_g:
                self.show_graph = not self.show_graph
            elif event.key == pygame.K_e:
                self.run_elbow_method()
            elif event.key == pygame.K_m:
                # Back to main menu
                self._sync_menu_from_game()
                self.scene = "menu"
            elif event.key == pygame.K_5:
                self.algorithm = "kmeans"
                self.algorithm_b = "kmedoids"
                self.reset_algorithm()
            elif event.key == pygame.K_6:
                self.algorithm = "kmedoids"
                self.algorithm_b = "kmeans"
                self.reset_algorithm()
            elif event.key == pygame.K_1:
                n = len(self.points) if self.points else 50
                self.generate_blobs(n)
                self.reset_algorithm()
            elif event.key == pygame.K_2:
                n = len(self.points) if self.points else 50
                self.generate_moons(n)
                self.reset_algorithm()
            elif event.key == pygame.K_3:
                n = len(self.points) if self.points else 50
                self.generate_circles(n)
                self.reset_algorithm()
            elif event.key == pygame.K_4:
                n = len(self.points) if self.points else 50
                self.generate_points(n)
                self.reset_algorithm()

        elif event.type == pygame.MOUSEBUTTONDOWN and not self.input_active:
            mx, my = pygame.mouse.get_pos()

            if event.button == 1:  # Left click - add point
                if my < HEIGHT - UI_PANEL_HEIGHT:
                    if self.battle_mode:
                        half = WIDTH // 2
                        if mx < half:
                            model_x = mx * 2
                        else:
                            model_x = (mx - half) * 2
                        model_x = max(80, min(WIDTH - 80, model_x))
                        new_a = Point(model_x, my)
                        new_b = Point(model_x, my)
                        self.points.append(new_a)
                        self.points_b.append(new_b)
                        self._invalidate_voronoi_cache()
                    else:
                        new_point = Point(mx, my)
                        self.points.append(new_point)
                        self.particles.append(ParticleEffect(mx, my, COLORS[random.randint(0, len(COLORS)-1)]))

            elif event.button == 3:  # Right click - move centroid
                if self.battle_mode:
                    half = WIDTH // 2
                    if mx < half:
                        model_x = mx * 2
                    else:
                        model_x = (mx - half) * 2
                    model_x = max(80, min(WIDTH - 80, model_x))

                    def move_nearest(centroids):
                        min_dist_sq = float("inf")
                        nearest = None
                        threshold_sq = 40 * 40
                        for c in centroids:
                            dx = c.x - model_x
                            dy = c.y - my
                            d = dx * dx + dy * dy
                            if d < min_dist_sq:
                                min_dist_sq = d
                                nearest = c
                        if nearest and min_dist_sq < threshold_sq:
                            nearest.target_x = model_x
                            nearest.target_y = my
                            nearest.x = model_x
                            nearest.y = my

                    move_nearest(self.centroids)
                    move_nearest(self.centroids_b)
                    self._invalidate_voronoi_cache()
                else:
                    min_dist_sq = float('inf')
                    nearest_centroid = None
                    threshold_sq = 40 * 40  # 40 pixels squared
                    
                    for centroid in self.centroids:
                        dist_sq = (centroid.x - mx)**2 + (centroid.y - my)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            nearest_centroid = centroid
                    
                    if nearest_centroid and min_dist_sq < threshold_sq:
                        nearest_centroid.target_x = mx
                        nearest_centroid.target_y = my
                        nearest_centroid.x = mx
                        nearest_centroid.y = my

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if self.scene == "menu":
                self.handle_menu_event(event)
            else:
                self.handle_game_event(event)
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.fps = self.clock.get_fps() if self.clock.get_fps() > 0 else 60
            current_time = pygame.time.get_ticks()
            
            self.handle_events()
            self.update()
            
            # Optimized: Use proper timer instead of modulo
            if self.scene == "game" and self.auto_iterate and (not self.converged or (self.battle_mode and not self.converged_b)):
                if current_time - self.last_iteration_time >= self.iteration_delay:
                    self.step_algorithm()
                    self.last_iteration_time = current_time
            
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = KMeansGame()
    game.run()