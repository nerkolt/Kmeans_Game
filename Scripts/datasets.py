import math
import random

from config import HEIGHT, SIDE_MARGIN, TOP_MARGIN, UI_PANEL_HEIGHT, WIDTH
from entities import Point


def _clamp_to_play_area(x, y):
    x = max(SIDE_MARGIN, min(WIDTH - SIDE_MARGIN, x))
    y = max(TOP_MARGIN, min(HEIGHT - UI_PANEL_HEIGHT - 20, y))
    return x, y


def generate_spaced_random_points(n, min_dist=25, max_tries_per_point=250):
    """Generate points with a minimum distance between them."""
    points = []
    min_dist_sq = min_dist * min_dist

    for _ in range(n):
        placed = False
        for _try in range(max_tries_per_point):
            x = random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN)
            y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)

            ok = True
            for p in points:
                dx = p.x - x
                dy = p.y - y
                if dx * dx + dy * dy < min_dist_sq:
                    ok = False
                    break

            if ok:
                points.append(Point(x, y))
                placed = True
                break

        if not placed:
            x = random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN)
            y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
            points.append(Point(x, y))

    return points


def generate_blobs(n, centers=3):
    points = []
    points_per_cluster = max(1, n // centers)
    margin = 100

    for _ in range(centers):
        center_x = random.randint(margin + 150, WIDTH - margin - 150)
        center_y = random.randint(margin + 100, HEIGHT - margin - 200)

        for _ in range(points_per_cluster):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.gauss(0, 40)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = max(margin, min(WIDTH - margin, x))
            y = max(margin, min(HEIGHT - margin - UI_PANEL_HEIGHT, y))
            points.append(Point(x, y))

    while len(points) < n:
        x = random.randint(SIDE_MARGIN, WIDTH - SIDE_MARGIN)
        y = random.randint(TOP_MARGIN, HEIGHT - UI_PANEL_HEIGHT - 20)
        points.append(Point(x, y))

    return points


def generate_moons(n):
    points = []
    half = n // 2

    for _ in range(half):
        angle = random.uniform(0, math.pi)
        radius = random.uniform(60, 100)
        x = WIDTH // 2 - 150 + radius * math.cos(angle)
        y = HEIGHT // 2 - 120 + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y)
        points.append(Point(x, y))

    for _ in range(n - half):
        angle = random.uniform(math.pi, 2 * math.pi)
        radius = random.uniform(60, 100)
        x = WIDTH // 2 + 150 + radius * math.cos(angle)
        y = HEIGHT // 2 + 30 + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y)
        points.append(Point(x, y))

    return points


def generate_circles(n):
    points = []
    center_x, center_y = WIDTH // 2, HEIGHT // 2 - 80
    inner = n // 3

    for _ in range(inner):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(30, 70)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y)
        points.append(Point(x, y))

    for _ in range(n - inner):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(120, 180)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y)
        points.append(Point(x, y))

    return points

