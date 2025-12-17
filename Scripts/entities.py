import math
import random

import pygame


class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.cluster = None
        self.prev_cluster = None
        self.transition = 0.0  # 0..1 for color transitions
        self.scale = 1.0
        self.trail = []

    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def distance_squared_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def update(self):
        # Smooth movement
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1

        # Color transition blending
        if self.transition < 1.0:
            self.transition = min(1.0, self.transition + 0.05)

        # Pulse effect
        if self.scale > 1.0:
            self.scale = max(1.0, self.scale - 0.05)

        # Trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)


class Centroid:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.color = color
        self.pulse = 0.0
        self.glow_radius = 0.0

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
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 1.0,
                    "color": color,
                }
            )

    def update(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.95
            p["vy"] *= 0.95
            p["life"] -= 0.03

        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw(self, screen):
        for p in self.particles:
            alpha = int(p["life"] * 255)
            color = (*p["color"], alpha)
            size = int(p["life"] * 4)
            if size <= 0:
                continue
            pos = (int(p["x"]), int(p["y"]))

            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            screen.blit(s, (pos[0] - size, pos[1] - size))


