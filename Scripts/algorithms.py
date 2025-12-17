import random

from entities import ParticleEffect


def assign_clusters(points, centroids, particles=None, max_particles_per_step=0):
    """Assign each point to the nearest centroid. Returns True if no assignments changed."""
    changes = 0
    particle_count = 0

    for point in points:
        min_dist_sq = float("inf")
        closest = 0

        for i, centroid in enumerate(centroids):
            dist_sq = point.distance_squared_to(centroid)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest = i

        if point.cluster != closest:
            changes += 1
            point.prev_cluster = point.cluster
            point.cluster = closest
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


def update_centroids(points, centroids):
    """Move centroids to the mean of their clusters."""
    for i, centroid in enumerate(centroids):
        cluster_points = [p for p in points if p.cluster == i]
        if cluster_points:
            mean_x = sum(p.x for p in cluster_points) / len(cluster_points)
            mean_y = sum(p.y for p in cluster_points) / len(cluster_points)
            centroid.x = mean_x
            centroid.y = mean_y
            centroid.target_x = mean_x
            centroid.target_y = mean_y


def calculate_inertia(points, centroids):
    """Within-Cluster Sum of Squares (WCSS) / Inertia."""
    total = 0
    for point in points:
        if point.cluster is not None:
            centroid = centroids[point.cluster]
            total += point.distance_squared_to(centroid)
    return total


def update_medoids(points, centroids, candidate_limit=25):
    """Update medoids (approximate PAM): pick a point minimizing intra-cluster distance."""
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

        if len(cluster_points) <= candidate_limit:
            candidates = cluster_points
        else:
            candidates = random.sample(cluster_points, candidate_limit)

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

