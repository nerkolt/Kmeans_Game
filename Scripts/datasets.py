import math
import random

import config
from entities import Point


def _clamp_to_play_area(x, y, width, height):
    x = max(config.SIDE_MARGIN, min(width - config.SIDE_MARGIN, x))
    y = max(config.TOP_MARGIN, min(height - config.UI_PANEL_HEIGHT - 20, y))
    return x, y


def generate_spaced_random_points(n, min_dist=25, max_tries_per_point=250, width=None, height=None):
    """Generate points with a minimum distance between them."""
    points = []
    min_dist_sq = min_dist * min_dist
    width = int(width if width is not None else config.WIDTH)
    height = int(height if height is not None else config.HEIGHT)

    for _ in range(n):
        placed = False
        for _try in range(max_tries_per_point):
            x = random.randint(config.SIDE_MARGIN, max(config.SIDE_MARGIN + 1, width - config.SIDE_MARGIN))
            y = random.randint(config.TOP_MARGIN, max(config.TOP_MARGIN + 1, height - config.UI_PANEL_HEIGHT - 20))

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
            x = random.randint(config.SIDE_MARGIN, max(config.SIDE_MARGIN + 1, width - config.SIDE_MARGIN))
            y = random.randint(config.TOP_MARGIN, max(config.TOP_MARGIN + 1, height - config.UI_PANEL_HEIGHT - 20))
            points.append(Point(x, y))

    return points


def generate_blobs(n, centers=3, width=None, height=None):
    width = int(width if width is not None else config.WIDTH)
    height = int(height if height is not None else config.HEIGHT)
    points = []
    points_per_cluster = max(1, n // centers)
    margin = 100

    for _ in range(centers):
        center_x = random.randint(margin + 150, max(margin + 151, width - margin - 150))
        center_y = random.randint(margin + 100, max(margin + 101, height - margin - 200))

        for _ in range(points_per_cluster):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.gauss(0, 40)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            x = max(margin, min(width - margin, x))
            y = max(margin, min(height - margin - config.UI_PANEL_HEIGHT, y))
            points.append(Point(x, y))

    while len(points) < n:
        x = random.randint(config.SIDE_MARGIN, max(config.SIDE_MARGIN + 1, width - config.SIDE_MARGIN))
        y = random.randint(config.TOP_MARGIN, max(config.TOP_MARGIN + 1, height - config.UI_PANEL_HEIGHT - 20))
        points.append(Point(x, y))

    return points


def generate_moons(n, width=None, height=None):
    width = int(width if width is not None else config.WIDTH)
    height = int(height if height is not None else config.HEIGHT)
    points = []
    half = n // 2

    for _ in range(half):
        angle = random.uniform(0, math.pi)
        radius = random.uniform(60, 100)
        x = width // 2 - 150 + radius * math.cos(angle)
        y = height // 2 - 120 + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y, width, height)
        points.append(Point(x, y))

    for _ in range(n - half):
        angle = random.uniform(math.pi, 2 * math.pi)
        radius = random.uniform(60, 100)
        x = width // 2 + 150 + radius * math.cos(angle)
        y = height // 2 + 30 + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y, width, height)
        points.append(Point(x, y))

    return points


def generate_circles(n, width=None, height=None):
    width = int(width if width is not None else config.WIDTH)
    height = int(height if height is not None else config.HEIGHT)
    points = []
    center_x, center_y = width // 2, height // 2 - 80
    inner = n // 3

    for _ in range(inner):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(30, 70)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y, width, height)
        points.append(Point(x, y))

    for _ in range(n - inner):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(120, 180)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        x, y = _clamp_to_play_area(x, y, width, height)
        points.append(Point(x, y))

    return points

