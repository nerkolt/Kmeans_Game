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
GRAY = (200, 200, 200)

# Colors for clusters
COLORS = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    (100, 100, 255),  # Blue
    (255, 255, 100),  # Yellow
    (255, 100, 255),  # Magenta
]

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cluster = None
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class Centroid:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

class KMeansGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("K-Means Clustering Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.points = []
        self.centroids = []
        self.k = 3
        self.running = True
        self.auto_iterate = False
        self.iteration_count = 0
        
        # Generate random points
        self.generate_points(50)
        self.reset_centroids()
    
    def generate_points(self, n):
        self.points = []
        for _ in range(n):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 100)
            self.points.append(Point(x, y))
    
    def reset_centroids(self):
        self.centroids = []
        for i in range(self.k):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 100)
            self.centroids.append(Centroid(x, y, COLORS[i % len(COLORS)]))
        self.iteration_count = 0
    
    def assign_clusters(self):
        """Assign each point to nearest centroid"""
        for point in self.points:
            min_dist = float('inf')
            closest_centroid = 0
            
            for i, centroid in enumerate(self.centroids):
                dist = point.distance_to(centroid)
                if dist < min_dist:
                    min_dist = dist
                    closest_centroid = i
            
            point.cluster = closest_centroid
    
    def update_centroids(self):
        """Move centroids to mean of their clusters"""
        for i, centroid in enumerate(self.centroids):
            cluster_points = [p for p in self.points if p.cluster == i]
            
            if cluster_points:
                mean_x = sum(p.x for p in cluster_points) / len(cluster_points)
                mean_y = sum(p.y for p in cluster_points) / len(cluster_points)
                centroid.x = mean_x
                centroid.y = mean_y
    
    def kmeans_step(self):
        """One iteration of K-Means"""
        self.assign_clusters()
        self.update_centroids()
        self.iteration_count += 1
    
    def draw(self):
        self.screen.fill(WHITE)
        
        # Draw points
        for point in self.points:
            if point.cluster is not None:
                color = self.centroids[point.cluster].color
            else:
                color = GRAY
            pygame.draw.circle(self.screen, color, (int(point.x), int(point.y)), 5)
        
        # Draw centroids
        for centroid in self.centroids:
            pygame.draw.circle(self.screen, BLACK, (int(centroid.x), int(centroid.y)), 12, 3)
            pygame.draw.circle(self.screen, centroid.color, (int(centroid.x), int(centroid.y)), 8)
        
        # Draw UI
        instructions = [
            "SPACE: Step K-Means | A: Auto-iterate | R: Reset",
            f"K={self.k} (UP/DOWN to change) | Iterations: {self.iteration_count}",
            "Click to add points | RIGHT CLICK to move centroid"
        ]
        
        y_offset = HEIGHT - 80
        for text in instructions:
            surface = self.small_font.render(text, True, BLACK)
            self.screen.blit(surface, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
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
                elif event.key == pygame.K_UP:
                    self.k = min(5, self.k + 1)
                    self.reset_centroids()
                elif event.key == pygame.K_DOWN:
                    self.k = max(1, self.k - 1)
                    self.reset_centroids()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if event.button == 1:  # Left click - add point
                    if my < HEIGHT - 100:  # Don't place in UI area
                        self.points.append(Point(mx, my))
                
                elif event.button == 3:  # Right click - move nearest centroid
                    min_dist = float('inf')
                    nearest_centroid = None
                    
                    for centroid in self.centroids:
                        dist = math.sqrt((centroid.x - mx)**2 + (centroid.y - my)**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_centroid = centroid
                    
                    if nearest_centroid and min_dist < 30:
                        nearest_centroid.x = mx
                        nearest_centroid.y = my
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            
            if self.auto_iterate:
                self.kmeans_step()
                pygame.time.delay(200)  # Slow down auto-iteration
            
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = KMeansGame()
    game.run()