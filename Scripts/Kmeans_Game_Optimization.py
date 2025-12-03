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
    
    def update(self):
        # Smooth movement
        self.x += (self.target_x - self.x) * 0.08
        self.y += (self.target_y - self.y) * 0.08
        
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
        pygame.display.set_caption("K-Means Clustering Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 22)
        
        self.points = []
        self.centroids = []
        self.particles = []
        self.k = 3
        self.running = True
        self.auto_iterate = False
        self.iteration_count = 0
        self.converged = False
        
        # Generate random points
        self.generate_points(50)
        self.reset_centroids()
    
    def generate_points(self, n):
        self.points = []
        for _ in range(n):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(80, HEIGHT - 140)
            self.points.append(Point(x, y))
    
    def reset_centroids(self):
        self.centroids = []
        for i in range(self.k):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(80, HEIGHT - 140)
            self.centroids.append(Centroid(x, y, COLORS[i % len(COLORS)]))
        self.iteration_count = 0
        self.converged = False
    
    def assign_clusters(self):
        """Assign each point to nearest centroid"""
        changes = 0
        for point in self.points:
            prev_cluster = point.cluster
            min_dist = float('inf')
            closest_centroid = 0
            
            for i, centroid in enumerate(self.centroids):
                dist = point.distance_to(centroid)
                if dist < min_dist:
                    min_dist = dist
                    closest_centroid = i
            
            if point.cluster != closest_centroid:
                changes += 1
                point.prev_cluster = point.cluster
                point.cluster = closest_centroid
                point.transition = 0
                point.scale = 1.5
                # Add particle effect
                if point.prev_cluster is not None:
                    self.particles.append(ParticleEffect(point.x, point.y, 
                                        self.centroids[point.cluster].color))
        
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
    
    def kmeans_step(self):
        """One iteration of K-Means"""
        if not self.converged:
            no_changes = self.assign_clusters()
            self.update_centroids()
            self.iteration_count += 1
            
            if no_changes:
                self.converged = True
    
    def draw_glow(self, pos, color, radius):
        """Draw a glowing circle effect"""
        for i in range(3, 0, -1):
            alpha = 40 * i
            glow_color = (*color, alpha)
            s = pygame.Surface((radius*2*i, radius*2*i), pygame.SRCALPHA)
            pygame.draw.circle(s, glow_color, (radius*i, radius*i), radius*i)
            self.screen.blit(s, (pos[0]-radius*i, pos[1]-radius*i))
    
    def lerp_color(self, c1, c2, t):
        """Linear interpolation between two colors"""
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    
    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Draw connections from points to centroids (faint lines)
        for point in self.points:
            if point.cluster is not None:
                centroid = self.centroids[point.cluster]
                color = (*centroid.color, 30)
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(s, color, (int(point.x), int(point.y)), 
                               (int(centroid.x), int(centroid.y)), 1)
                self.screen.blit(s, (0, 0))
        
        # Draw centroid glows
        for centroid in self.centroids:
            self.draw_glow((int(centroid.x), int(centroid.y)), 
                          centroid.color, int(centroid.glow_radius))
        
        # Draw trails for points
        for point in self.points:
            if len(point.trail) > 1 and point.cluster is not None:
                color = self.centroids[point.cluster].color
                for i in range(len(point.trail) - 1):
                    alpha = int((i / len(point.trail)) * 100)
                    trail_color = (*color, alpha)
                    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(s, trail_color, point.trail[i], point.trail[i+1], 2)
                    self.screen.blit(s, (0, 0))
        
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
        
        # Draw UI panel
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
            "SPACE: Step  |  A: Auto  |  R: Reset  |  ↑↓: Change K",
            f"Clusters: {self.k}  |  Iterations: {self.iteration_count}  |  Points: {len(self.points)}",
            "LEFT CLICK: Add point  |  RIGHT CLICK: Move centroid"
        ]
        
        y_offset = HEIGHT - 100
        for text in controls:
            surface = self.small_font.render(text, True, TEXT_COLOR)
            self.screen.blit(surface, (20, y_offset))
            y_offset += 28
        
        pygame.display.flip()
    
    def update(self):
        # Update all animations
        for point in self.points:
            point.update()
        
        for centroid in self.centroids:
            centroid.update()
        
        for particle in self.particles:
            particle.update()
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.particles]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.kmeans_step()
                elif event.key == pygame.K_a:
                    self.auto_iterate = not self.auto_iterate
                elif event.key == pygame.K_r:
                    self.reset_centroids()
                    for point in self.points:
                        point.cluster = None
                        point.prev_cluster = None
                elif event.key == pygame.K_UP:
                    self.k = min(5, self.k + 1)
                    self.reset_centroids()
                elif event.key == pygame.K_DOWN:
                    self.k = max(1, self.k - 1)
                    self.reset_centroids()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click - add point
                    if my < HEIGHT - 120:
                        new_point = Point(mx, my)
                        self.points.append(new_point)
                        self.particles.append(ParticleEffect(mx, my, COLORS[random.randint(0, len(COLORS)-1)]))
                
                elif event.button == 3:  # Right click - move centroid
                    min_dist = float('inf')
                    nearest_centroid = None
                    
                    for centroid in self.centroids:
                        dist = math.sqrt((centroid.x - mx)**2 + (centroid.y - my)**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_centroid = centroid
                    
                    if nearest_centroid and min_dist < 40:
                        nearest_centroid.target_x = mx
                        nearest_centroid.target_y = my
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            
            if self.auto_iterate and not self.converged:
                if pygame.time.get_ticks() % 15 == 0:  # Slow down iterations
                    self.kmeans_step()
            
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = KMeansGame()
    game.run()