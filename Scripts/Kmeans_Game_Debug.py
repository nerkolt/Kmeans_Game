import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
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

        # Algorithm selection
        self.algorithm = "kmeans"  # "kmeans" or "kmedoids"

        # K-Medoids settings (keep it interactive; exact PAM can be heavy for 500 pts)
        self.kmedoids_candidate_limit = 25  # sample candidates per cluster when large

        # Main menu state
        self.menu_index = 0
        self.menu_algorithm = self.algorithm
        self.menu_dataset = "random"  # random/blobs/moons/circles
        self.menu_points = 50
        self.menu_k = self.k
        
        # Generate random points
        self.generate_points(50)
        self.reset_algorithm()

    def _sync_menu_from_game(self):
        self.menu_algorithm = self.algorithm
        self.menu_points = len(self.points) if self.points else 50
        self.menu_k = self.k
        self.menu_dataset = self.dataset_type if self.dataset_type else "random"

    def _apply_menu_settings_and_start(self):
        self.algorithm = self.menu_algorithm
        self.k = self.menu_k

        # Generate dataset using chosen point count
        n = int(self.menu_points)
        if self.menu_dataset == "blobs":
            self.generate_blobs(n)
        elif self.menu_dataset == "moons":
            self.generate_moons(n)
        elif self.menu_dataset == "circles":
            self.generate_circles(n)
        else:
            self.generate_points(n)

        # Reset algorithm state + assignments
        self.reset_algorithm()

        # Reset UI toggles for a clean start
        self.auto_iterate = False
        self.show_elbow = False
        self.elbow_data = []

        self.scene = "game"
    
    def _generate_spaced_points(self, n, min_dist=25, max_tries_per_point=200):
        """Generate points with a minimum distance between them."""
        self.points = []
        min_dist_sq = min_dist * min_dist
        
        for _ in range(n):
            placed = False
            for _try in range(max_tries_per_point):
                x = random.randint(80, WIDTH - 80)
                y = random.randint(80, HEIGHT - 140)
                
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
                y = random.randint(80, HEIGHT - 140)
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
            y = random.randint(80, HEIGHT - 140)
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
            y = max(80, min(HEIGHT - 140, y))
            self.points.append(Point(x, y))
        
        # Second moon (lower)
        for i in range(n - half):
            angle = random.uniform(math.pi, 2 * math.pi)
            radius = random.uniform(60, 100)
            x = WIDTH // 2 + 150 + radius * math.cos(angle)
            y = HEIGHT // 2 + 50 + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(80, min(HEIGHT - 140, y))
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
            y = max(80, min(HEIGHT - 140, y))
            self.points.append(Point(x, y))
        
        # Outer circle
        for i in range(n - n // 3):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(120, 180)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = max(80, min(WIDTH - 80, x))
            y = max(80, min(HEIGHT - 140, y))
            self.points.append(Point(x, y))
        
        self.dataset_type = "circles"
    
    def reset_centroids(self):
        self.centroids = []
        for i in range(self.k):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(80, HEIGHT - 140)
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
        if self.algorithm == "kmedoids":
            self.reset_medoids()
        else:
            self.reset_centroids()

        # Reset point assignments
        for point in self.points:
            point.cluster = None
            point.prev_cluster = None

    def step_algorithm(self):
        """Run one step of the currently selected algorithm."""
        if self.algorithm == "kmedoids":
            self.kmedoids_step()
        else:
            self.kmeans_step()
    
    def assign_clusters(self):
        """Assign each point to nearest centroid"""
        changes = 0
        particle_count = 0
        max_particles_per_step = 10  # Limit particle effects
        
        for point in self.points:
            prev_cluster = point.cluster
            min_dist_sq = float('inf')
            closest_centroid = 0
            
            for i, centroid in enumerate(self.centroids):
                # Use squared distance to avoid expensive sqrt
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
                # Add particle effect (limited to prevent performance issues)
                if point.prev_cluster is not None and particle_count < max_particles_per_step:
                    self.particles.append(ParticleEffect(point.x, point.y, 
                                        self.centroids[point.cluster].color))
                    particle_count += 1
        
        return changes == 0
    
    def update_centroids(self):
        """Move centroids to mean of their clusters"""
        for i, centroid in enumerate(self.centroids):
            cluster_points = [p for p in self.points if p.cluster == i]
            
            if cluster_points:
                mean_x = sum(p.x for p in cluster_points) / len(cluster_points)
                mean_y = sum(p.y for p in cluster_points) / len(cluster_points)
                # Move instantly during algorithm steps for responsiveness
                centroid.x = mean_x
                centroid.y = mean_y
                centroid.target_x = mean_x
                centroid.target_y = mean_y
    
    def calculate_inertia(self):
        """Calculate Within-Cluster Sum of Squares (WCSS) / Inertia"""
        total = 0
        for point in self.points:
            if point.cluster is not None:
                centroid = self.centroids[point.cluster]
                total += point.distance_squared_to(centroid)
        return total
    
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
        if not self.points:
            return

        for i, centroid in enumerate(self.centroids):
            cluster_points = [p for p in self.points if p.cluster == i]
            if not cluster_points:
                # Re-seed empty cluster medoid
                p = random.choice(self.points)
                centroid.x = p.x
                centroid.y = p.y
                centroid.target_x = p.x
                centroid.target_y = p.y
                continue

            # Candidate set: exact for small clusters, sampled for large clusters
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
    
    def draw(self):
        if self.scene == "menu":
            self.draw_main_menu()
            pygame.display.flip()
            return

        self.screen.fill(BG_COLOR)
        
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
        panel_rect = pygame.Rect(0, HEIGHT - 120, WIDTH, 120)
        pygame.draw.rect(self.screen, UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLORS[0], panel_rect, 2)
        
        # Draw status
        status_text = "CONVERGED ✓" if self.converged else ("AUTO" if self.auto_iterate else "PAUSED")
        status_color = COLORS[1] if self.converged else (COLORS[2] if self.auto_iterate else TEXT_COLOR)
        status = self.font.render(status_text, True, status_color)
        self.screen.blit(status, (WIDTH - 180, HEIGHT - 105))
        
        # Draw controls
        controls = [
            "SPACE: Step  |  A: Auto  |  R: Reset  |  D: Debug  |  C: Clear",
            f"P: Points  |  K: Clusters  |  M: Main Menu  |  5/6: Algo  |  S: Stats  |  G: Graph  |  E: Elbow  |  Iter: {self.iteration_count}",
            "1: Blobs  |  2: Moons  |  3: Circles  |  4: Random  |  Click: Add/Move"
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

        title = self.font.render("Data Mining Mini-Project", True, COLORS[1])
        subtitle = self.small_font.render("Clustering Visualizer", True, TEXT_COLOR)
        self.screen.blit(title, (20, 20))
        self.screen.blit(subtitle, (20, 55))

        # Menu items
        algo_label = "K-Means" if self.menu_algorithm == "kmeans" else "K-Medoids"
        dataset_label = self.menu_dataset.capitalize()
        items = [
            ("Algorithm", algo_label),
            ("Dataset", dataset_label),
            ("Points", str(self.menu_points)),
            ("K (clusters)", str(self.menu_k)),
            ("Start", "ENTER"),
            ("Quit", "ESC"),
        ]

        box = pygame.Rect(20, 95, WIDTH - 40, 360)
        pygame.draw.rect(self.screen, UI_BG, box, border_radius=12)
        pygame.draw.rect(self.screen, COLORS[3], box, 2, border_radius=12)

        y = box.y + 18
        for idx, (k, v) in enumerate(items):
            selected = (idx == self.menu_index)
            color = COLORS[2] if selected else TEXT_COLOR
            left = self.small_font.render(f"{k}:", True, color)
            right = self.small_font.render(v, True, COLORS[1] if selected else TEXT_COLOR)
            self.screen.blit(left, (box.x + 18, y))
            self.screen.blit(right, (box.x + 220, y))
            if selected:
                pygame.draw.rect(self.screen, (*COLORS[2],), (box.x + 10, y - 4, box.width - 20, 28), 1, border_radius=6)
            y += 40

        help_lines = [
            "UP/DOWN: select   LEFT/RIGHT: change value",
            "ENTER: start game   ESC: quit   M: open menu from inside the game",
            "Quick keys: 1-4 dataset, 5/6 algorithm",
        ]
        y2 = HEIGHT - 105
        for line in help_lines:
            s = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(s, (20, y2))
            y2 += 28
    
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
            ("", TEXT_COLOR),
            ("Cluster Sizes:", COLORS[2]),
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
        panel_height = max(150, min(panel_height, HEIGHT - 140))  # Leave space for bottom UI
        
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
    
    def draw_convergence_graph(self):
        """Draw a graph showing inertia over iterations"""
        graph_width = 300
        graph_height = 150
        graph_x = 10
        graph_y = 10
        
        if len(self.inertia_history) < 2:
            return
        
        # Background
        s = pygame.Surface((graph_width, graph_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*UI_BG, 240), (0, 0, graph_width, graph_height))
        pygame.draw.rect(s, COLORS[2], (0, 0, graph_width, graph_height), 2)
        self.screen.blit(s, (graph_x, graph_y))
        
        # Title
        title = self.tiny_font.render("Convergence Graph (Inertia)", True, COLORS[2])
        self.screen.blit(title, (graph_x + 5, graph_y + 5))
        
        # Draw graph
        if len(self.inertia_history) > 1:
            max_inertia = max(self.inertia_history)
            min_inertia = min(self.inertia_history)
            range_inertia = max_inertia - min_inertia if max_inertia != min_inertia else 1
            
            graph_padding = 30
            plot_width = graph_width - graph_padding * 2
            plot_height = graph_height - graph_padding * 2
            
            points = []
            for i, inertia in enumerate(self.inertia_history):
                x = graph_x + graph_padding + (i / (len(self.inertia_history) - 1)) * plot_width
                normalized = (inertia - min_inertia) / range_inertia
                y = graph_y + graph_padding + plot_height - (normalized * plot_height)
                points.append((x, y))
            
            # Draw line
            if len(points) > 1:
                pygame.draw.lines(self.screen, COLORS[1], False, points, 2)
            
            # Draw current value
            if self.inertia_history:
                current = self.inertia_history[-1]
                value_text = self.tiny_font.render(f"Current: {int(current)}", True, COLORS[1])
                self.screen.blit(value_text, (graph_x + 5, graph_y + graph_height - 20))
    
    def draw_elbow_method(self):
        """Draw elbow method visualizer (K vs Inertia)"""
        if not self.elbow_data:
            return
        
        panel_width = 280
        panel_height = 200
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
        panel_y = HEIGHT - 350
        
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
    
    def handle_menu_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        items_count = 6  # Algorithm, Dataset, Points, K, Start, Quit

        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if event.key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % items_count
            return
        if event.key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % items_count
            return

        # Quick keys (work anywhere in menu)
        if event.key == pygame.K_5:
            self.menu_algorithm = "kmeans"
            return
        if event.key == pygame.K_6:
            self.menu_algorithm = "kmedoids"
            return
        if event.key == pygame.K_1:
            self.menu_dataset = "blobs"
            return
        if event.key == pygame.K_2:
            self.menu_dataset = "moons"
            return
        if event.key == pygame.K_3:
            self.menu_dataset = "circles"
            return
        if event.key == pygame.K_4:
            self.menu_dataset = "random"
            return

        if event.key == pygame.K_RETURN:
            if self.menu_index == 4:  # Start
                self._apply_menu_settings_and_start()
            return

        # LEFT/RIGHT adjust selected values
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            delta = -1 if event.key == pygame.K_LEFT else 1

            if self.menu_index == 0:  # Algorithm
                self.menu_algorithm = "kmedoids" if self.menu_algorithm == "kmeans" else "kmeans"
            elif self.menu_index == 1:  # Dataset
                order = ["random", "blobs", "moons", "circles"]
                i = order.index(self.menu_dataset) if self.menu_dataset in order else 0
                self.menu_dataset = order[(i + delta) % len(order)]
            elif self.menu_index == 2:  # Points
                self.menu_points = max(1, min(500, self.menu_points + (10 * delta)))
            elif self.menu_index == 3:  # K
                self.menu_k = max(1, min(10, self.menu_k + delta))
            elif self.menu_index == 5:  # Quit
                if delta != 0:
                    self.running = False

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
                self.reset_algorithm()
            elif event.key == pygame.K_6:
                self.algorithm = "kmedoids"
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
                if my < HEIGHT - 120:
                    new_point = Point(mx, my)
                    self.points.append(new_point)
                    self.particles.append(ParticleEffect(mx, my, COLORS[random.randint(0, len(COLORS)-1)]))

            elif event.button == 3:  # Right click - move centroid
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
            if self.scene == "game" and self.auto_iterate and not self.converged:
                if current_time - self.last_iteration_time >= self.iteration_delay:
                    self.step_algorithm()
                    self.last_iteration_time = current_time
            
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = KMeansGame()
    game.run()