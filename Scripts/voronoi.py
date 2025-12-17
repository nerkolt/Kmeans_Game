import pygame


class VoronoiCache:
    def __init__(self):
        self.key = None
        self.surface = None

    def invalidate(self):
        self.key = None
        self.surface = None


def get_voronoi_surface(centroids, cache: VoronoiCache, view_w, view_h, cell_size=12, x_scale=1.0, alpha=45):
    """Return a cached Voronoi/decision-region surface for the given centroids."""
    if not centroids or view_w <= 0 or view_h <= 0:
        return None

    cell = max(4, int(cell_size))
    centroid_key = tuple((int(c.x), int(c.y), idx) for idx, c in enumerate(centroids))
    key = (view_w, view_h, cell, round(x_scale, 3), centroid_key, alpha)

    if cache.key == key and cache.surface is not None:
        return cache.surface

    s = pygame.Surface((view_w, view_h), pygame.SRCALPHA)

    for y in range(0, view_h, cell):
        for x in range(0, view_w, cell):
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

    cache.key = key
    cache.surface = s
    return s

