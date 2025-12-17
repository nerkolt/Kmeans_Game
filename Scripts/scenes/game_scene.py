import math
import os
import random

import pygame

import algorithms
import csv_io
import datasets
import voronoi
import config
from entities import Centroid, ParticleEffect, Point


class GameScene:
    def __init__(self, app, settings):
        self.app = app

        self.points = []
        self.centroids = []
        self.particles = []

        self.points_b = []
        self.centroids_b = []
        self.particles_b = []

        self.k = int(settings.get("k", 3))
        self.algorithm = settings.get("algorithm", "kmeans")  # kmeans/kmedoids/dbscan
        if self.algorithm == "kmeans":
            self.algorithm_b = "kmedoids"
        elif self.algorithm == "kmedoids":
            self.algorithm_b = "kmeans"
        else:
            self.algorithm_b = "kmeans"
        self.dataset_type = settings.get("dataset", "random")

        self.battle_mode = bool(settings.get("battle_mode", False))
        self.show_voronoi = bool(settings.get("voronoi", False))

        self.csv_points = list(settings.get("csv_points", []))

        # Tutorial / learning mode
        self.tutorial_mode = bool(settings.get("tutorial", False))
        self.tutorial_page = 0
        self._tutorial_flash = ""
        self._tutorial_flash_until = 0

        # DBSCAN params (pixels)
        self.dbscan_eps = int(settings.get("dbscan_eps", 45))
        self.dbscan_min_samples = int(settings.get("dbscan_min_samples", 5))
        self._dbscan_clusters_a = 0
        self._dbscan_clusters_b = 0

        self.auto_iterate = False
        self.iteration_count = 0
        self.iteration_count_b = 0
        self.converged = False
        self.converged_b = False

        self.show_debug = True
        self.show_stats = False
        self.show_graph = False
        self.show_elbow = False

        self.inertia_history = []
        self.inertia_history_b = []
        self.elbow_data = []

        # Performance: timer-based auto iteration
        self.last_iteration_time = 0
        self.iteration_delay = 300  # ms (slower, more "game-like")

        # Point spacing (slows convergence + reduces overlap)
        self.min_point_distance = 25
        self.max_tries_per_point = 250

        # K-medoids settings
        self.kmedoids_candidate_limit = 25

        # Input dialog (points / k)
        self.input_active = False
        self.input_text = ""
        self.input_field = "points"

        # Voronoi cache
        self.voronoi_cell_size = 12
        self._vor_cache_a = voronoi.VoronoiCache()
        self._vor_cache_b = voronoi.VoronoiCache()

        self._load_initial_dataset(int(settings.get("points", 50)))
        self.reset_algorithm()

    # -----------------------
    # Dataset / initialization
    # -----------------------
    def _load_initial_dataset(self, n):
        n = max(1, int(n))
        if self.dataset_type == "csv":
            if not self.csv_points:
                self.dataset_type = "random"
                self.points = datasets.generate_spaced_random_points(
                    n, min_dist=self.min_point_distance, max_tries_per_point=self.max_tries_per_point
                )
            else:
                self.points = self._points_from_xy(self.csv_points)
        elif self.dataset_type == "blobs":
            self.points = datasets.generate_blobs(n, centers=max(2, min(5, self.k)))
        elif self.dataset_type == "moons":
            self.points = datasets.generate_moons(n)
        elif self.dataset_type == "circles":
            self.points = datasets.generate_circles(n)
        else:
            self.dataset_type = "random"
            self.points = datasets.generate_spaced_random_points(
                n, min_dist=self.min_point_distance, max_tries_per_point=self.max_tries_per_point
            )

        if self.battle_mode:
            self.points_b = [Point(p.x, p.y) for p in self.points]

    def _points_from_xy(self, xy):
        # Fit raw (x,y) into play area with scaling.
        if not xy:
            return []
        xs = [p[0] for p in xy]
        ys = [p[1] for p in xy]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        dx = (max_x - min_x) if max_x != min_x else 1.0
        dy = (max_y - min_y) if max_y != min_y else 1.0

        play_left = config.SIDE_MARGIN
        play_right = config.WIDTH - config.SIDE_MARGIN
        play_top = config.TOP_MARGIN
        play_bottom = config.HEIGHT - config.UI_PANEL_HEIGHT - 20
        play_w = max(1, play_right - play_left)
        play_h = max(1, play_bottom - play_top)

        pts = []
        for x, y in xy:
            nx = (float(x) - min_x) / dx
            ny = (float(y) - min_y) / dy
            px = play_left + nx * play_w
            py = play_top + ny * play_h
            pts.append(Point(px, py))
        return pts

    # -----------------------
    # Algorithm lifecycle
    # -----------------------
    def _invalidate_voronoi_cache(self):
        self._vor_cache_a.invalidate()
        self._vor_cache_b.invalidate()

    def _reset_centroids(self, into_list, coords=None):
        into_list.clear()
        coords = coords or []
        for i in range(self.k):
            if i < len(coords):
                x, y = coords[i]
            elif self.points:
                p = random.choice(self.points)
                x, y = p.x, p.y
            else:
                x = random.randint(config.SIDE_MARGIN, config.WIDTH - config.SIDE_MARGIN)
                y = random.randint(config.TOP_MARGIN, config.HEIGHT - config.UI_PANEL_HEIGHT - 20)
            into_list.append(Centroid(x, y, config.COLORS[i % len(config.COLORS)]))

    def reset_algorithm(self):
        # Shared centroid starting positions (fair for battle mode) for centroid-based algorithms.
        coords = []
        for i in range(self.k):
            if self.points:
                p = random.choice(self.points)
                coords.append((p.x, p.y))
            else:
                coords.append(
                    (
                        random.randint(config.SIDE_MARGIN, config.WIDTH - config.SIDE_MARGIN),
                        random.randint(config.TOP_MARGIN, config.HEIGHT - config.UI_PANEL_HEIGHT - 20),
                    )
                )

        if self.algorithm in ("kmeans", "kmedoids"):
            self._reset_centroids(self.centroids, coords=coords)
        else:
            self.centroids.clear()

        if self.battle_mode:
            if self.algorithm_b in ("kmeans", "kmedoids"):
                self._reset_centroids(self.centroids_b, coords=coords)
            else:
                self.centroids_b.clear()
        else:
            self.centroids_b.clear()

        # Clear assignments & counters
        for p in self.points:
            p.cluster = None
            p.prev_cluster = None
            p.transition = 0
        for p in self.points_b:
            p.cluster = None
            p.prev_cluster = None
            p.transition = 0

        self.particles.clear()
        self.particles_b.clear()

        self.iteration_count = 0
        self.iteration_count_b = 0
        self.converged = False
        self.converged_b = False
        self.inertia_history = []
        self.inertia_history_b = []
        self.elbow_data = []
        self.show_elbow = False
        self._dbscan_clusters_a = 0
        self._dbscan_clusters_b = 0

        self._invalidate_voronoi_cache()

    def _step_side(self, points, centroids, particles, algorithm_name, inertia_history):
        if not points:
            return True

        if algorithm_name == "dbscan":
            # DBSCAN is one-shot (no iterative centroid updates)
            clusters = algorithms.dbscan(points, eps=self.dbscan_eps, min_samples=self.dbscan_min_samples)
            if points is self.points:
                self._dbscan_clusters_a = clusters
            else:
                self._dbscan_clusters_b = clusters
            return True

        if not centroids:
            return True

        no_changes = algorithms.assign_clusters(points, centroids, particles=particles, max_particles_per_step=10)

        if algorithm_name == "kmedoids":
            algorithms.update_medoids(points, centroids, candidate_limit=self.kmedoids_candidate_limit)
        else:
            algorithms.update_centroids(points, centroids)

        inertia = algorithms.calculate_inertia(points, centroids)
        inertia_history.append(inertia)

        return no_changes

    def step_algorithm(self):
        if self.converged and (not self.battle_mode or self.converged_b):
            return

        if not self.converged:
            self.converged = self._step_side(self.points, self.centroids, self.particles, self.algorithm, self.inertia_history)
            self.iteration_count += 1

        if self.battle_mode and not self.converged_b:
            self.converged_b = self._step_side(
                self.points_b, self.centroids_b, self.particles_b, self.algorithm_b, self.inertia_history_b
            )
            self.iteration_count_b += 1

        self._invalidate_voronoi_cache()

    def enable_battle_mode(self):
        if self.battle_mode:
            return
        self.battle_mode = True
        if self.algorithm == "kmeans":
            self.algorithm_b = "kmedoids"
        elif self.algorithm == "kmedoids":
            self.algorithm_b = "kmeans"
        else:
            self.algorithm_b = "kmeans"
        self.points_b = [Point(p.x, p.y) for p in self.points]
        self.reset_algorithm()

    def disable_battle_mode(self):
        self.battle_mode = False
        self.points_b.clear()
        self.centroids_b.clear()
        self.particles_b.clear()
        self.converged_b = False
        self.iteration_count_b = 0
        self.inertia_history_b = []
        self._invalidate_voronoi_cache()

    # -----------------------
    # Tutorial / learning mode
    # -----------------------
    def _set_tutorial_flash(self, msg, seconds=2.0):
        self._tutorial_flash = msg
        self._tutorial_flash_until = pygame.time.get_ticks() + int(seconds * 1000)

    def _wrap_text(self, font, text, max_w):
        words = str(text).split(" ")
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _algo_pretty(self, key):
        if key == "kmeans":
            return "K-Means"
        if key == "kmedoids":
            return "K-Medoids"
        if key == "dbscan":
            return "DBSCAN"
        return str(key)

    def _draw_tutorial_overlay(self):
        if not self.tutorial_mode:
            return

        screen = self.app.screen
        pad = 14
        w = 430
        x = 10
        y = 10

        title = "LEARNING MODE"
        hint = "Keys: [T] toggle  |  [TAB] next page  |  [SHIFT+TAB] prev page"

        page = self.tutorial_page % 3
        if page == 0:
            lines = [
                ("What you see", config.COLORS[2 % len(config.COLORS)]),
                ("- Points are your data samples.", config.TEXT_COLOR),
                ("- Colors show cluster assignment.", config.TEXT_COLOR),
                ("- Lines show point → centroid/medoid assignment.", config.TEXT_COLOR),
                ("- SPACE runs 1 step, A runs auto until convergence.", config.TEXT_COLOR),
                ("", config.TEXT_COLOR),
                ("Try this:", config.COLORS[3 % len(config.COLORS)]),
                ("1) Press 1 (Blobs), set K≈#blobs, then press A.", config.TEXT_COLOR),
                ("2) Press 2 (Moons) and compare K-Means vs DBSCAN.", config.TEXT_COLOR),
            ]
        elif page == 1:
            lines = [
                ("K-Means / K-Medoids", config.COLORS[2 % len(config.COLORS)]),
                ("Each iteration has 2 phases:", config.TEXT_COLOR),
                ("1) Assign: each point chooses its nearest center.", config.TEXT_COLOR),
                ("2) Update: centers move (mean for K-Means, medoid for K-Medoids).", config.TEXT_COLOR),
                ("Convergence happens when assignments stop changing.", config.TEXT_COLOR),
                ("", config.TEXT_COLOR),
                ("Tip:", config.COLORS[3 % len(config.COLORS)]),
                ("- K-Means prefers round/spherical clusters.", config.TEXT_COLOR),
                ("- K-Medoids is more robust to outliers.", config.TEXT_COLOR),
            ]
        else:
            lines = [
                ("DBSCAN (density-based)", config.COLORS[2 % len(config.COLORS)]),
                ("DBSCAN does NOT use K.", config.TEXT_COLOR),
                ("It groups points by density using:", config.TEXT_COLOR),
                (f"- eps: radius = {self.dbscan_eps}px", config.TEXT_COLOR),
                (f"- min_samples: {self.dbscan_min_samples}", config.TEXT_COLOR),
                ("Points labeled -1 are noise/outliers.", config.TEXT_COLOR),
                ("", config.TEXT_COLOR),
                ("Tip:", config.COLORS[3 % len(config.COLORS)]),
                ("- Moons/Circles often look better with DBSCAN than K-Means.", config.TEXT_COLOR),
            ]

        # Build dynamic height
        font = self.app.tiny_font
        max_text_w = w - pad * 2
        wrapped = []
        for txt, col in lines:
            if not txt:
                wrapped.append(("", col))
                continue
            for line in self._wrap_text(font, txt, max_text_w):
                wrapped.append((line, col))

        flash = None
        if self._tutorial_flash and pygame.time.get_ticks() < self._tutorial_flash_until:
            flash = self._tutorial_flash

        h = pad * 2 + (len(wrapped) + 4) * (font.get_height() + 4)
        if flash:
            h += (font.get_height() + 10)
        h = min(h, 420)

        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 160), (0, 0, w, h), border_radius=12)
        pygame.draw.rect(s, (80, 80, 110, 200), (0, 0, w, h), 2, border_radius=12)
        screen.blit(s, (x, y))

        ty = y + pad
        screen.blit(self.app.small_font.render(title, True, config.COLORS[1 % len(config.COLORS)]), (x + pad, ty))
        ty += self.app.small_font.get_height() + 4
        screen.blit(font.render(hint, True, config.COLORS[4 % len(config.COLORS)]), (x + pad, ty))
        ty += font.get_height() + 10

        # Current context line
        algo = self._algo_pretty(self.algorithm)
        ctx = f"Algo: {algo}  |  Mode: {'BATTLE' if self.battle_mode else 'SINGLE'}  |  Dataset: {self.dataset_type.upper()}"
        screen.blit(font.render(ctx, True, config.TEXT_COLOR), (x + pad, ty))
        ty += font.get_height() + 10

        for txt, col in wrapped:
            if ty > y + h - pad - (font.get_height() + 4):
                break
            if txt:
                screen.blit(font.render(txt, True, col), (x + pad, ty))
            ty += font.get_height() + 4

        if flash and ty <= y + h - pad - (font.get_height() + 4):
            ty += 6
            screen.blit(font.render(flash, True, config.COLORS[0]), (x + pad, ty))

    # -----------------------
    # Data mining helpers
    # -----------------------
    def calculate_inertia(self):
        return algorithms.calculate_inertia(self.points, self.centroids) if self.points and self.centroids else 0

    def _clone_points(self, pts):
        out = []
        for p in pts:
            np = Point(p.x, p.y)
            np.cluster = p.cluster
            np.prev_cluster = p.prev_cluster
            out.append(np)
        return out

    def _reset_centroids_for(self, pts, k):
        cents = []
        for i in range(k):
            if pts:
                p = random.choice(pts)
                x, y = p.x, p.y
            else:
                x = random.randint(config.SIDE_MARGIN, config.WIDTH - config.SIDE_MARGIN)
                y = random.randint(config.TOP_MARGIN, config.HEIGHT - config.UI_PANEL_HEIGHT - 20)
            cents.append(Centroid(x, y, config.COLORS[i % len(config.COLORS)]))
        return cents

    def run_elbow_method(self):
        if not self.points:
            return

        original_k = self.k
        original_points = self._clone_points(self.points)
        original_centroids = [Centroid(c.x, c.y, c.color) for c in self.centroids]
        original_algorithm = self.algorithm
        original_clusters = [p.cluster for p in self.points]

        self.elbow_data = []
        self.algorithm = "kmeans"

        max_k = min(10, len(self.points))
        for test_k in range(1, max_k + 1):
            tmp_points = self._clone_points(original_points)
            tmp_centroids = self._reset_centroids_for(tmp_points, test_k)

            # reset assignments
            for p in tmp_points:
                p.cluster = None
                p.prev_cluster = None

            for _ in range(50):
                done = algorithms.assign_clusters(tmp_points, tmp_centroids, particles=None, max_particles_per_step=0)
                algorithms.update_centroids(tmp_points, tmp_centroids)
                if done:
                    break

            inertia = algorithms.calculate_inertia(tmp_points, tmp_centroids)
            self.elbow_data.append((test_k, inertia))

        # restore
        self.k = original_k
        self.algorithm = original_algorithm
        self.points = original_points
        self.centroids = original_centroids
        for i, p in enumerate(self.points):
            p.cluster = original_clusters[i] if i < len(original_clusters) else None

        self.show_elbow = True
        self._invalidate_voronoi_cache()

    def calculate_cluster_metrics(self):
        # Only meaningful for centroid-based clustering.
        if self.algorithm == "dbscan" or not self.centroids:
            return {}
        metrics = {}
        for i in range(self.k):
            cluster_points = [p for p in self.points if p.cluster == i]
            if not cluster_points:
                continue
            centroid = self.centroids[i]
            distances = [p.distance_to(centroid) for p in cluster_points]
            avg_dist = sum(distances) / len(distances) if distances else 0
            variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances) if distances else 0
            metrics[i] = {
                "size": len(cluster_points),
                "avg_distance": avg_dist,
                "variance": variance,
                "compactness": 1.0 / (1.0 + variance),
            }
        return metrics

    # -----------------------
    # CSV I/O
    # -----------------------
    def import_points_from_csv(self):
        root = csv_io.project_root(__file__)
        path = csv_io.ask_open_csv_path(initialdir=root)
        if not path:
            return False
        xy = csv_io.read_xy_from_csv(path)
        if not xy:
            return False

        self.csv_points = xy
        self.dataset_type = "csv"
        self.points = self._points_from_xy(xy)
        if self.battle_mode:
            self.points_b = [Point(p.x, p.y) for p in self.points]
        self.reset_algorithm()
        return True

    def export_points_to_csv(self):
        root = csv_io.project_root(__file__)
        default_name = csv_io.default_export_name("clustering_export")
        path = csv_io.ask_save_csv_path(initialdir=root, default_name=default_name)
        if not path:
            return False

        rows = []
        for p in self.points:
            rows.append((float(p.x), float(p.y), p.cluster if p.cluster is not None else "", "A", self.algorithm))
        if self.battle_mode:
            for p in self.points_b:
                rows.append((float(p.x), float(p.y), p.cluster if p.cluster is not None else "", "B", self.algorithm_b))

        csv_io.write_points_csv(path, rows, header=["x", "y", "cluster", "side", "algorithm"])
        return True

    # -----------------------
    # Input / events
    # -----------------------
    def _back_to_menu(self):
        from scenes.menu_scene import MenuScene

        initial = {
            "algorithm": self.algorithm,
            "dataset": self.dataset_type,
            "points": len(self.points) if self.points else 50,
            "k": self.k,
            "start_mode": "battle" if self.battle_mode else "single",
            "voronoi": self.show_voronoi,
            "csv_points": list(self.csv_points),
        }
        self.app.set_scene(MenuScene(self.app, initial=initial))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Input dialog
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    try:
                        value = int(self.input_text)
                        if self.input_field == "points":
                            if 1 <= value <= 500:
                                self._load_initial_dataset(value)
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

            # Controls
            if event.key == pygame.K_t:
                self.tutorial_mode = not self.tutorial_mode
                self._set_tutorial_flash("Learning mode ON" if self.tutorial_mode else "Learning mode OFF", seconds=1.4)
            elif event.key == pygame.K_TAB:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self.tutorial_page = (self.tutorial_page - 1) % 3
                else:
                    self.tutorial_page = (self.tutorial_page + 1) % 3
            elif event.key == pygame.K_SPACE:
                self.step_algorithm()
                if self.tutorial_mode and (self.algorithm in ("kmeans", "kmedoids")):
                    self._set_tutorial_flash("Step = Assign → Update (one full iteration).", seconds=2.0)
            elif event.key == pygame.K_a:
                self.auto_iterate = not self.auto_iterate
                if self.tutorial_mode and self.auto_iterate:
                    self._set_tutorial_flash("Tip: try SPACE step-by-step first, then A for auto.", seconds=2.5)
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
                self.import_points_from_csv()
            elif event.key == pygame.K_o:
                self.export_points_to_csv()
            elif event.key == pygame.K_c:
                self.points.clear()
                self.particles.clear()
                self.converged = False
                if self.battle_mode:
                    self.points_b.clear()
                    self.particles_b.clear()
                    self.converged_b = False
                self._invalidate_voronoi_cache()
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
                self._back_to_menu()
            elif event.key == pygame.K_5:
                self.algorithm = "kmeans"
                self.algorithm_b = "kmedoids"
                self.reset_algorithm()
            elif event.key == pygame.K_6:
                self.algorithm = "kmedoids"
                self.algorithm_b = "kmeans"
                self.reset_algorithm()
            elif event.key == pygame.K_7:
                self.algorithm = "dbscan"
                self.algorithm_b = "kmeans"
                self.reset_algorithm()
            elif event.key == pygame.K_1:
                n = len(self.points) if self.points else 50
                self.dataset_type = "blobs"
                self.points = datasets.generate_blobs(n, centers=max(2, min(5, self.k)))
                if self.battle_mode:
                    self.points_b = [Point(p.x, p.y) for p in self.points]
                self.reset_algorithm()
            elif event.key == pygame.K_2:
                n = len(self.points) if self.points else 50
                self.dataset_type = "moons"
                self.points = datasets.generate_moons(n)
                if self.battle_mode:
                    self.points_b = [Point(p.x, p.y) for p in self.points]
                self.reset_algorithm()
            elif event.key == pygame.K_3:
                n = len(self.points) if self.points else 50
                self.dataset_type = "circles"
                self.points = datasets.generate_circles(n)
                if self.battle_mode:
                    self.points_b = [Point(p.x, p.y) for p in self.points]
                self.reset_algorithm()
            elif event.key == pygame.K_4:
                n = len(self.points) if self.points else 50
                self.dataset_type = "random"
                self.points = datasets.generate_spaced_random_points(
                    n, min_dist=self.min_point_distance, max_tries_per_point=self.max_tries_per_point
                )
                if self.battle_mode:
                    self.points_b = [Point(p.x, p.y) for p in self.points]
                self.reset_algorithm()

        elif event.type == pygame.MOUSEBUTTONDOWN and not self.input_active:
            mx, my = pygame.mouse.get_pos()
            w, h = self.app.screen.get_size()
            if my >= h - config.UI_PANEL_HEIGHT:
                return

            # Left click adds point; right click moves nearest centroid
            if event.button == 1:
                if self.battle_mode:
                    half = w // 2
                    model_x = mx * 2 if mx < half else (mx - half) * 2
                    model_x = max(config.SIDE_MARGIN, min(w - config.SIDE_MARGIN, model_x))
                    new_a = Point(model_x, my)
                    new_b = Point(model_x, my)
                    self.points.append(new_a)
                    self.points_b.append(new_b)
                    self._invalidate_voronoi_cache()
                else:
                    self.points.append(Point(mx, my))
                    self.particles.append(
                        ParticleEffect(mx, my, config.COLORS[random.randint(0, len(config.COLORS) - 1)])
                    )
            elif event.button == 3:
                threshold_sq = 40 * 40
                if self.battle_mode:
                    half = w // 2
                    model_x = mx * 2 if mx < half else (mx - half) * 2
                    model_x = max(config.SIDE_MARGIN, min(w - config.SIDE_MARGIN, model_x))

                    def move_nearest(centroids):
                        min_dist_sq = float("inf")
                        nearest = None
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
                    min_dist_sq = float("inf")
                    nearest = None
                    for c in self.centroids:
                        dx = c.x - mx
                        dy = c.y - my
                        d = dx * dx + dy * dy
                        if d < min_dist_sq:
                            min_dist_sq = d
                            nearest = c
                    if nearest and min_dist_sq < threshold_sq:
                        nearest.target_x = mx
                        nearest.target_y = my
                        nearest.x = mx
                        nearest.y = my
                        self._invalidate_voronoi_cache()

    # -----------------------
    # Update / draw
    # -----------------------
    def update(self, dt_ms):
        # Animations
        for p in self.points:
            p.update()
        for c in self.centroids:
            c.update()
        for pe in self.particles:
            pe.update()
        self.particles = [p for p in self.particles if p.particles]

        if self.battle_mode:
            for p in self.points_b:
                p.update()
            for c in self.centroids_b:
                c.update()
            for pe in self.particles_b:
                pe.update()
            self.particles_b = [p for p in self.particles_b if p.particles]

        # Auto iteration timer
        if self.auto_iterate and (not self.converged or (self.battle_mode and not self.converged_b)):
            now = pygame.time.get_ticks()
            if now - self.last_iteration_time >= self.iteration_delay:
                self.step_algorithm()
                self.last_iteration_time = now

    def _draw_glow(self, color, pos, radius):
        r = int(max(4, radius))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, 70), (r, r), r)
        self.app.screen.blit(s, (pos[0] - r, pos[1] - r))

    def _draw_model_view(self, points, centroids, particles, view_rect, x_scale, vor_cache, side_label, status_lines=None):
        screen = self.app.screen

        def dbscan_color_for_cluster(cid):
            # Noise
            if cid == -1:
                return (120, 120, 135)
            # Reuse palette first, then deterministic extra colors.
            if cid < len(config.COLORS):
                return config.COLORS[cid]
            # Deterministic pseudo-random color based on cid (no global RNG state)
            r = (37 * cid + 90) % 220 + 30
            g = (57 * cid + 140) % 220 + 30
            b = (93 * cid + 60) % 220 + 30
            return (r, g, b)

        # Decision regions
        if self.show_voronoi:
            vs = voronoi.get_voronoi_surface(
                centroids,
                cache=vor_cache,
                view_w=view_rect.w,
                view_h=view_rect.h,
                cell_size=self.voronoi_cell_size,
                x_scale=x_scale,
                alpha=45,
            )
            if vs is not None:
                screen.blit(vs, (view_rect.x, view_rect.y))

        # Draw trails and connection lines on dedicated surfaces (perf)
        trail_surface = pygame.Surface((view_rect.w, view_rect.h), pygame.SRCALPHA)
        connection_surface = pygame.Surface((view_rect.w, view_rect.h), pygame.SRCALPHA)

        # Connections
        # Connection lines are core to understanding assignments, so they should not
        # depend on debug-panel visibility.
        if centroids:
            for p in points:
                if p.cluster is None:
                    continue
                c = centroids[p.cluster]
                x1 = int(p.x * x_scale)
                y1 = int(p.y)
                x2 = int(c.x * x_scale)
                y2 = int(c.y)
                pygame.draw.line(connection_surface, (*c.color, 40), (x1, y1), (x2, y2), 1)

        # Trails + points
        for p in points:
            col = (170, 170, 180)
            if centroids and p.cluster is not None and 0 <= p.cluster < len(centroids):
                col = centroids[p.cluster].color
            elif (not centroids) and (p.cluster is not None):
                # DBSCAN mode: cluster ids live on the points (no centroids)
                try:
                    cid = int(p.cluster)
                except Exception:
                    cid = -1
                col = dbscan_color_for_cluster(cid)

            # Trails
            if len(p.trail) > 1:
                pts = [(int(tx * x_scale), int(ty)) for (tx, ty) in p.trail]
                for i in range(1, len(pts)):
                    a = int(20 + (i / len(pts)) * 70)
                    pygame.draw.line(trail_surface, (*col, a), pts[i - 1], pts[i], 2)

            # Point
            px = view_rect.x + int(p.x * x_scale)
            py = view_rect.y + int(p.y)
            radius = int(6 * p.scale)
            pygame.draw.circle(screen, col, (px, py), radius)
            pygame.draw.circle(screen, (0, 0, 0), (px, py), radius, 1)

        screen.blit(trail_surface, (view_rect.x, view_rect.y))
        screen.blit(connection_surface, (view_rect.x, view_rect.y))

        # Centroids
        for i, c in enumerate(centroids):
            cx = view_rect.x + int(c.x * x_scale)
            cy = view_rect.y + int(c.y)
            self._draw_glow(c.color, (cx, cy), c.glow_radius)
            pygame.draw.circle(screen, c.color, (cx, cy), 10)
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 10, 2)
            txt = self.app.tiny_font.render(str(i + 1), True, (0, 0, 0))
            screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

        # Particles
        for pe in particles:
            pe.draw(screen, x_scale=x_scale, x_offset=view_rect.x, y_offset=view_rect.y)

        # Side label
        label = self.app.small_font.render(side_label, True, config.TEXT_COLOR)
        screen.blit(label, (view_rect.x + 10, view_rect.y + 10))

        # Status badge(s) near the model (important in battle mode)
        if status_lines:
            pad_x = 10
            pad_y = 8
            gap = 4
            lines = [(txt, col) for (txt, col) in status_lines if txt]
            if lines:
                widths = [self.app.tiny_font.size(t)[0] for (t, _c) in lines]
                height = self.app.tiny_font.get_height()
                box_w = max(widths) + pad_x * 2
                box_h = (len(lines) * height) + ((len(lines) - 1) * gap) + pad_y * 2

                x = view_rect.right - box_w - 10
                y = view_rect.y + 8

                s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                pygame.draw.rect(s, (0, 0, 0, 140), (0, 0, box_w, box_h), border_radius=10)
                pygame.draw.rect(s, (80, 80, 110, 200), (0, 0, box_w, box_h), 1, border_radius=10)
                screen.blit(s, (x, y))

                ty = y + pad_y
                for txt, col in lines:
                    surf = self.app.tiny_font.render(txt, True, col)
                    screen.blit(surf, (x + pad_x, ty))
                    ty += height + gap

    def draw_input_dialog(self):
        dialog_width = 460
        dialog_height = 170
        w, h = self.app.screen.get_size()
        dialog_x = (w - dialog_width) // 2
        dialog_y = (h - dialog_height) // 2

        shadow = pygame.Surface((dialog_width + 12, dialog_height + 12), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (0, 0, dialog_width + 12, dialog_height + 12), border_radius=12)
        self.app.screen.blit(shadow, (dialog_x - 6, dialog_y - 6))

        pygame.draw.rect(self.app.screen, config.UI_BG, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=10)
        pygame.draw.rect(
            self.app.screen,
            config.COLORS[2 % len(config.COLORS)],
            (dialog_x, dialog_y, dialog_width, dialog_height),
            3,
            border_radius=10,
        )

        title = "Enter Number of Points" if self.input_field == "points" else "Enter Number of Clusters (K)"
        title_s = self.app.font.render(title, True, config.TEXT_COLOR)
        self.app.screen.blit(title_s, (dialog_x + 20, dialog_y + 18))

        input_box = pygame.Rect(dialog_x + 20, dialog_y + 65, dialog_width - 40, 46)
        pygame.draw.rect(self.app.screen, config.BG_COLOR, input_box, border_radius=8)
        pygame.draw.rect(self.app.screen, config.COLORS[1 % len(config.COLORS)], input_box, 2, border_radius=8)

        txt = self.input_text + "|"
        txt_s = self.app.font.render(txt, True, config.TEXT_COLOR)
        self.app.screen.blit(txt_s, (input_box.x + 12, input_box.y + 8))

        hint = "ENTER: confirm   ESC: cancel   BACKSPACE: delete"
        hint_s = self.app.menu_hint_font.render(hint, True, config.COLORS[3 % len(config.COLORS)])
        self.app.screen.blit(hint_s, (dialog_x + 20, dialog_y + 125))

    def draw_convergence_graph_for(self, history, graph_x, graph_y, border_color, line_color, title_text):
        graph_width = 320
        graph_height = 160
        if history is None or len(history) < 2:
            return

        s = pygame.Surface((graph_width, graph_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*config.UI_BG, 240), (0, 0, graph_width, graph_height), border_radius=10)
        pygame.draw.rect(s, border_color, (0, 0, graph_width, graph_height), 2, border_radius=10)
        self.app.screen.blit(s, (graph_x, graph_y))

        title = self.app.tiny_font.render(title_text, True, border_color)
        self.app.screen.blit(title, (graph_x + 8, graph_y + 8))

        max_inertia = max(history)
        min_inertia = min(history)
        rng = max_inertia - min_inertia if max_inertia != min_inertia else 1

        pad = 32
        plot_w = graph_width - pad * 2
        plot_h = graph_height - pad * 2

        pts = []
        for i, inertia in enumerate(history):
            x = graph_x + pad + (i / (len(history) - 1)) * plot_w
            norm = (inertia - min_inertia) / rng
            y = graph_y + pad + plot_h - (norm * plot_h)
            pts.append((x, y))

        if len(pts) > 1:
            pygame.draw.lines(self.app.screen, line_color, False, pts, 2)

        cur = history[-1]
        cur_s = self.app.tiny_font.render(f"{int(cur)}", True, line_color)
        self.app.screen.blit(cur_s, (graph_x + 8, graph_y + graph_height - 22))

    def draw_convergence_graph(self):
        w, _h = self.app.screen.get_size()
        if self.battle_mode:
            self.draw_convergence_graph_for(
                self.inertia_history,
                10,
                40,
                config.COLORS[2 % len(config.COLORS)],
                config.COLORS[1 % len(config.COLORS)],
                "A: Inertia",
            )
            self.draw_convergence_graph_for(
                self.inertia_history_b,
                w - 330,
                40,
                config.COLORS[0],
                config.COLORS[1 % len(config.COLORS)],
                "B: Inertia",
            )
        else:
            self.draw_convergence_graph_for(
                self.inertia_history,
                10,
                10,
                config.COLORS[2 % len(config.COLORS)],
                config.COLORS[1 % len(config.COLORS)],
                "Convergence (Inertia)",
            )

    def draw_elbow_method(self):
        if not self.elbow_data or len(self.elbow_data) < 2:
            return

        panel_width = 340
        panel_height = 240
        w, h = self.app.screen.get_size()
        panel_x = w - panel_width - 10
        panel_y = h - config.UI_PANEL_HEIGHT - panel_height - 10

        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*config.UI_BG, 240), (0, 0, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(s, config.COLORS[0], (0, 0, panel_width, panel_height), 2, border_radius=10)
        self.app.screen.blit(s, (panel_x, panel_y))

        title = self.app.small_font.render("Elbow Method (K vs Inertia)", True, config.COLORS[0])
        self.app.screen.blit(title, (panel_x + 12, panel_y + 10))

        max_inertia = max(v for _, v in self.elbow_data)
        min_inertia = min(v for _, v in self.elbow_data)
        rng = max_inertia - min_inertia if max_inertia != min_inertia else 1

        pad = 44
        plot_w = panel_width - pad * 2
        plot_h = panel_height - pad * 2

        pts = []
        for i, (k, inertia) in enumerate(self.elbow_data):
            x = panel_x + pad + (i / (len(self.elbow_data) - 1)) * plot_w
            norm = (inertia - min_inertia) / rng
            y = panel_y + pad + plot_h - (norm * plot_h)
            pts.append((x, y))

        if len(pts) > 1:
            pygame.draw.lines(self.app.screen, config.COLORS[1 % len(config.COLORS)], False, pts, 2)
        for i, (k, inertia) in enumerate(self.elbow_data):
            x, y = pts[i]
            pygame.draw.circle(self.app.screen, config.COLORS[1 % len(config.COLORS)], (int(x), int(y)), 4)
            ks = self.app.tiny_font.render(f"K={k}", True, config.TEXT_COLOR)
            self.app.screen.blit(ks, (int(x) - 10, int(y) + 6))

    def draw_stats_panel(self):
        if self.algorithm == "dbscan":
            return
        panel_width = 300
        panel_x = 10
        _w, h = self.app.screen.get_size()
        panel_y = h - config.UI_PANEL_HEIGHT - 340

        metrics = self.calculate_cluster_metrics()
        inertia = self.calculate_inertia()

        min_sep = float("inf")
        for i in range(self.k):
            for j in range(i + 1, self.k):
                if i >= len(self.centroids) or j >= len(self.centroids):
                    continue
                dx = self.centroids[i].x - self.centroids[j].x
                dy = self.centroids[i].y - self.centroids[j].y
                d = math.sqrt(dx * dx + dy * dy)
                min_sep = min(min_sep, d)
        if min_sep == float("inf"):
            min_sep = 0

        lines = 6 + len(metrics) * 4
        panel_height = min(420, lines * 18 + 20)

        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*config.UI_BG, 240), (0, 0, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(s, config.COLORS[4 % len(config.COLORS)], (0, 0, panel_width, panel_height), 2, border_radius=10)
        self.app.screen.blit(s, (panel_x, panel_y))

        y = panel_y + 10
        title = self.app.small_font.render("ADVANCED STATS", True, config.COLORS[4 % len(config.COLORS)])
        self.app.screen.blit(title, (panel_x + 10, y))
        y += 26

        for txt, col in [
            (f"Inertia (WCSS): {int(inertia)}", config.COLORS[1 % len(config.COLORS)]),
            (f"Min Separation: {int(min_sep)}", config.TEXT_COLOR),
            ("", config.TEXT_COLOR),
            ("Per-Cluster:", config.COLORS[2 % len(config.COLORS)]),
        ]:
            if txt:
                surf = self.app.tiny_font.render(txt, True, col)
                self.app.screen.blit(surf, (panel_x + 10, y))
            y += 18

        for i, m in metrics.items():
            if i >= len(self.centroids):
                continue
            block = [
                (f"Cluster {i+1}:", self.centroids[i].color),
                (f"  Size: {m['size']}", config.TEXT_COLOR),
                (f"  Avg Dist: {m['avg_distance']:.1f}", config.TEXT_COLOR),
                (f"  Compactness: {m['compactness']:.2f}", config.TEXT_COLOR),
            ]
            for txt, col in block:
                surf = self.app.tiny_font.render(txt, True, col)
                self.app.screen.blit(surf, (panel_x + 10, y))
                y += 18

    def _draw_debug_panel(self):
        # Responsive debug panel (auto height based on content)
        if not self.show_debug:
            return

        lines = [
            ("DEBUG", config.COLORS[3 % len(config.COLORS)]),
            (f"FPS: {int(self.app.fps)}", config.TEXT_COLOR),
            (f"Algo A: {self.algorithm}", config.TEXT_COLOR),
            (f"K: {self.k}", config.TEXT_COLOR),
            (f"DBSCAN eps: {self.dbscan_eps}", config.TEXT_COLOR),
            (f"DBSCAN min: {self.dbscan_min_samples}", config.TEXT_COLOR),
            (f"Auto: {'On' if self.auto_iterate else 'Off'}", config.TEXT_COLOR),
            (f"Converged: {'Yes' if self.converged else 'No'}", config.TEXT_COLOR),
        ]
        if self.battle_mode:
            lines += [
                (f"Algo B: {self.algorithm_b}", config.TEXT_COLOR),
                (f"Conv B: {'Yes' if self.converged_b else 'No'}", config.TEXT_COLOR),
            ]

        panel_w = 240
        pad = 10
        line_h = 18
        panel_h = min(260, max(110, pad * 2 + len(lines) * line_h))
        w, _h = self.app.screen.get_size()
        panel_x = w - panel_w - 10
        panel_y = 10

        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*config.UI_BG, 240), (0, 0, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(s, config.COLORS[3 % len(config.COLORS)], (0, 0, panel_w, panel_h), 2, border_radius=10)
        self.app.screen.blit(s, (panel_x, panel_y))

        y = panel_y + pad
        for txt, col in lines:
            surf = self.app.tiny_font.render(txt, True, col)
            self.app.screen.blit(surf, (panel_x + pad, y))
            y += line_h

    def draw(self):
        screen = self.app.screen
        w, h = screen.get_size()
        screen.fill(config.BG_COLOR)

        play_h = h - config.UI_PANEL_HEIGHT
        play_rect = pygame.Rect(0, 0, w, play_h)

        # Draw play area border
        pygame.draw.rect(screen, (25, 25, 34), play_rect)

        if self.battle_mode:
            half = w // 2
            left_view = pygame.Rect(0, 0, half, play_h)
            right_view = pygame.Rect(half, 0, half, play_h)
            a_done = self.converged
            b_done = self.converged_b
            mode_tag = "AUTO" if self.auto_iterate else "MANUAL"
            a_color = config.COLORS[1 % len(config.COLORS)] if a_done else config.COLORS[0]
            b_color = config.COLORS[1 % len(config.COLORS)] if b_done else config.COLORS[0]
            a_state = "CONVERGED ✓" if a_done else "RUNNING"
            b_state = "CONVERGED ✓" if b_done else "RUNNING"

            a_extra = None
            if self.algorithm == "dbscan":
                noise_a = sum(1 for p in self.points if p.cluster == -1)
                a_extra = f"eps={self.dbscan_eps}  min={self.dbscan_min_samples}  clusters={self._dbscan_clusters_a}  noise={noise_a}"

            b_extra = None
            if self.algorithm_b == "dbscan":
                noise_b = sum(1 for p in self.points_b if p.cluster == -1)
                b_extra = f"eps={self.dbscan_eps}  min={self.dbscan_min_samples}  clusters={self._dbscan_clusters_b}  noise={noise_b}"

            self._draw_model_view(
                self.points,
                self.centroids,
                self.particles,
                left_view,
                0.5,
                self._vor_cache_a,
                f"A: {self.algorithm}",
                status_lines=[
                    (f"{mode_tag} | {a_state}", a_color),
                    (f"Iter: {self.iteration_count}", config.TEXT_COLOR),
                    (a_extra, config.TEXT_COLOR),
                ],
            )
            self._draw_model_view(
                self.points_b,
                self.centroids_b,
                self.particles_b,
                right_view,
                0.5,
                self._vor_cache_b,
                f"B: {self.algorithm_b}",
                status_lines=[
                    (f"{mode_tag} | {b_state}", b_color),
                    (f"Iter: {self.iteration_count_b}", config.TEXT_COLOR),
                    (b_extra, config.TEXT_COLOR),
                ],
            )
            pygame.draw.line(screen, (80, 80, 110), (half, 0), (half, play_h), 2)
        else:
            done = self.converged
            mode_tag = "AUTO" if self.auto_iterate else "MANUAL"
            state_color = config.COLORS[1 % len(config.COLORS)] if done else config.COLORS[0]
            state = "CONVERGED ✓" if done else "RUNNING"
            extra = None
            if self.algorithm == "dbscan":
                noise = sum(1 for p in self.points if p.cluster == -1)
                extra = f"eps={self.dbscan_eps}  min={self.dbscan_min_samples}  clusters={self._dbscan_clusters_a}  noise={noise}"
            self._draw_model_view(
                self.points,
                self.centroids,
                self.particles,
                play_rect,
                1.0,
                self._vor_cache_a,
                f"{self.algorithm}",
                status_lines=[
                    (f"{mode_tag} | {state}", state_color),
                    (f"Iter: {self.iteration_count}", config.TEXT_COLOR),
                    (extra, config.TEXT_COLOR),
                ],
            )

        # Graphs / overlays
        if self.show_graph:
            self.draw_convergence_graph()
        if self.show_elbow:
            self.draw_elbow_method()
        if self.show_stats:
            self.draw_stats_panel()
        self._draw_debug_panel()
        self._draw_tutorial_overlay()

        # Bottom UI bar
        ui_rect = pygame.Rect(0, h - config.UI_PANEL_HEIGHT, w, config.UI_PANEL_HEIGHT)
        pygame.draw.rect(screen, config.UI_BG, ui_rect)
        pygame.draw.line(screen, (80, 80, 110), (0, ui_rect.y), (w, ui_rect.y), 2)

        # Responsive HUD: header + two columns (wrap as needed)
        fully_converged = self.converged and (not self.battle_mode or self.converged_b)
        status_color = config.COLORS[1 % len(config.COLORS)] if fully_converged else config.COLORS[0]
        status_text = "CONVERGED ✓" if fully_converged else ("AUTO" if self.auto_iterate else "PAUSED")

        if self.algorithm == "kmeans":
            algo_a = "K-Means"
        elif self.algorithm == "kmedoids":
            algo_a = "K-Medoids"
        else:
            algo_a = "DBSCAN"
        if self.battle_mode:
            if self.algorithm_b == "kmeans":
                algo_b = "K-Means"
            elif self.algorithm_b == "kmedoids":
                algo_b = "K-Medoids"
            else:
                algo_b = "DBSCAN"
            mode_text = f"BATTLE  |  A: {algo_a} vs B: {algo_b}"
        else:
            mode_text = f"SINGLE  |  Algo: {algo_a}"

        header_left = f"{status_text}  |  Dataset: {self.dataset_type.upper()}  |  Voronoi: {'ON' if self.show_voronoi else 'OFF'}"
        header_y = ui_rect.y + 10
        screen.blit(self.app.small_font.render(header_left, True, status_color), (20, header_y))
        right_header = self.app.small_font.render(mode_text, True, config.TEXT_COLOR)
        screen.blit(right_header, (ui_rect.right - right_header.get_width() - 20, header_y))

        # Columns
        left_x = 20
        col_gap = 25
        right_x = ui_rect.x + int(ui_rect.w * 0.62) + col_gap
        left_w = int(ui_rect.w * 0.62) - col_gap - 20
        right_w = ui_rect.right - right_x - 20

        def wrap(font, text, max_w):
            words = text.split(" ")
            lines = []
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if font.size(test)[0] <= max_w:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        # Keybinds (clear + scannable)
        controls_left = [
            "CORE: [SPACE] Step  [A] Auto  [R] Reset  [M] Menu  [D] Debug  [C] Clear",
            "DATASETS: [1] Blobs  [2] Moons  [3] Circles  [4] Random",
            "ALGO: [5] K-Means  [6] K-Medoids  [7] DBSCAN   VIEW: [V] Voronoi  [B] Battle  [T] Tutorial",
            "ANALYSIS: [G] Graph  [S] Stats  [E] Elbow   CSV: [I] Import  [O] Export   MOUSE: L-Click add  R-Click move",
        ]

        left_lines = []
        for line in controls_left:
            left_lines += wrap(self.app.tiny_font, line, left_w)

        inertia_a = int(algorithms.calculate_inertia(self.points, self.centroids)) if self.points and self.centroids else 0
        stats_right = [
            f"K={self.k}",
            f"IterA={self.iteration_count}  ConvA={'Y' if self.converged else 'N'}",
            f"InertiaA={inertia_a}",
        ]
        if self.battle_mode:
            inertia_b = int(algorithms.calculate_inertia(self.points_b, self.centroids_b)) if self.points_b and self.centroids_b else 0
            stats_right += [
                f"IterB={self.iteration_count_b}  ConvB={'Y' if self.converged_b else 'N'}",
                f"InertiaB={inertia_b}",
            ]

        right_lines = []
        for line in stats_right:
            right_lines += wrap(self.app.tiny_font, line, right_w)

        content_top = header_y + self.app.small_font.get_height() + 10
        bottom_pad = 10
        available_h = ui_rect.bottom - bottom_pad - content_top
        line_h = max(self.app.tiny_font.get_height() + 4, 18)
        max_lines = max(len(left_lines), len(right_lines), 1)
        if max_lines * line_h > available_h:
            line_h = max(16, available_h // max_lines)

        y = content_top
        for i in range(max_lines):
            if y + line_h > ui_rect.bottom - bottom_pad:
                break
            if i < len(left_lines):
                screen.blit(self.app.tiny_font.render(left_lines[i], True, config.TEXT_COLOR), (left_x, y))
            if i < len(right_lines):
                screen.blit(self.app.tiny_font.render(right_lines[i], True, config.TEXT_COLOR), (right_x, y))
            y += line_h

        if self.input_active:
            self.draw_input_dialog()

        pygame.display.flip()


