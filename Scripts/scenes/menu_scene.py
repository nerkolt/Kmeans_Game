import random
import time

import pygame

import csv_io
import datasets
import config


class MenuScene:
    """
    Accessible main menu:
    - Keyboard: UP/DOWN select, LEFT/RIGHT change, ENTER activate
    - Mouse: click rows to select; click actions to activate
    - Shortcuts: 1-4 datasets, 5/6/7 algorithms, B battle, V voronoi, I import, O export
    """

    def __init__(self, app, initial=None):
        self.app = app

        initial = initial or {}

        self.menu_index = 0
        self.menu_algorithm = initial.get("algorithm", "kmeans")  # kmeans/kmedoids/dbscan
        self.menu_dataset = initial.get("dataset", "random")  # random/blobs/moons/circles/csv
        self.menu_points = int(initial.get("points", 50))
        self.menu_k = int(initial.get("k", 3))
        self.menu_start_mode = initial.get("start_mode", "single")  # single/battle
        self.menu_voronoi = bool(initial.get("voronoi", False))
        self.menu_tutorial = bool(initial.get("tutorial", False))
        self.menu_dbscan_eps = int(initial.get("dbscan_eps", 45))
        self.menu_dbscan_min_samples = int(initial.get("dbscan_min_samples", 5))

        self.csv_points = list(initial.get("csv_points", []))  # list[(x,y)]

        self.menu_message = ""
        self.menu_message_until = 0

        self._menu_layout_cache = None
        self._preview_cache_key = None
        self._preview_xy = []

        self._regen_preview()

    def _set_message(self, msg, seconds=2.2):
        self.menu_message = msg
        self.menu_message_until = pygame.time.get_ticks() + int(seconds * 1000)

    def _get_items(self):
        return [
            {
                "key": "algorithm",
                "type": "choice",
                "label": "Algorithm (A)",
                "value": self.menu_algorithm,
                "choices": [("kmeans", "K-Means"), ("kmedoids", "K-Medoids"), ("dbscan", "DBSCAN")],
            },
            {
                "key": "dataset",
                "type": "choice",
                "label": "Dataset",
                "value": self.menu_dataset,
                "choices": [
                    ("random", "Random"),
                    ("blobs", "Blobs"),
                    ("moons", "Moons"),
                    ("circles", "Circles"),
                    ("csv", "CSV"),
                ],
            },
            {"key": "points", "type": "int", "label": "Points", "value": self.menu_points, "min": 1, "max": 500, "step": 5},
            {"key": "k", "type": "int", "label": "Clusters (K)", "value": self.menu_k, "min": 1, "max": 10, "step": 1},
            {"key": "dbscan_eps", "type": "int", "label": "DBSCAN eps (px)", "value": self.menu_dbscan_eps, "min": 5, "max": 200, "step": 5},
            {
                "key": "dbscan_min_samples",
                "type": "int",
                "label": "DBSCAN min_samples",
                "value": self.menu_dbscan_min_samples,
                "min": 2,
                "max": 30,
                "step": 1,
            },
            {
                "key": "start_mode",
                "type": "choice",
                "label": "Mode",
                "value": self.menu_start_mode,
                "choices": [("single", "Single"), ("battle", "Battle (A/B)")],
            },
            {"key": "voronoi", "type": "bool", "label": "Voronoi regions", "value": self.menu_voronoi},
            {"key": "tutorial", "type": "bool", "label": "Learning mode (Tutorial)", "value": self.menu_tutorial},
            {"key": "import", "type": "action", "label": "Import CSV", "value": None},
            {"key": "export", "type": "action", "label": "Export CSV", "value": None},
            {"key": "start", "type": "action", "label": "Start", "value": None},
            {"key": "quit", "type": "action", "label": "Quit", "value": None},
        ]

    def _apply_item_value(self, key, value):
        if key == "algorithm":
            self.menu_algorithm = value
        elif key == "dataset":
            self.menu_dataset = value
        elif key == "points":
            self.menu_points = int(value)
        elif key == "k":
            self.menu_k = int(value)
        elif key == "start_mode":
            self.menu_start_mode = value
        elif key == "voronoi":
            self.menu_voronoi = bool(value)
        elif key == "tutorial":
            self.menu_tutorial = bool(value)
        elif key == "dbscan_eps":
            self.menu_dbscan_eps = int(value)
        elif key == "dbscan_min_samples":
            self.menu_dbscan_min_samples = int(value)

        self._regen_preview()

    def _regen_preview(self):
        key = (self.menu_dataset, self.menu_points, len(self.csv_points))
        if self._preview_cache_key == key:
            return
        self._preview_cache_key = key

        if self.menu_dataset == "csv":
            self._preview_xy = list(self.csv_points)
            return

        n = max(10, min(150, int(self.menu_points)))
        w, h = self.app.screen.get_size()
        if self.menu_dataset == "random":
            pts = datasets.generate_spaced_random_points(n, width=w, height=h)
        elif self.menu_dataset == "blobs":
            pts = datasets.generate_blobs(n, centers=max(2, min(5, self.menu_k)), width=w, height=h)
        elif self.menu_dataset == "moons":
            pts = datasets.generate_moons(n, width=w, height=h)
        elif self.menu_dataset == "circles":
            pts = datasets.generate_circles(n, width=w, height=h)
        else:
            pts = datasets.generate_spaced_random_points(n, width=w, height=h)

        self._preview_xy = [(p.x, p.y) for p in pts]

    def _do_import_csv(self):
        root = csv_io.project_root(__file__)
        path = csv_io.ask_open_csv_path(initialdir=root)
        if not path:
            return False
        xy = csv_io.read_xy_from_csv(path)
        if not xy:
            return False
        self.csv_points = xy
        self._apply_item_value("dataset", "csv")
        return True

    def _do_export_csv(self):
        root = csv_io.project_root(__file__)
        default_name = csv_io.default_export_name("menu_preview")
        path = csv_io.ask_save_csv_path(initialdir=root, default_name=default_name)
        if not path:
            return False
        rows = [(float(x), float(y)) for (x, y) in self._preview_xy]
        csv_io.write_points_csv(path, rows, header=["x", "y"])
        return True

    def _start(self):
        if self.menu_dataset == "csv" and not self.csv_points:
            self._set_message("No CSV loaded. Import first (I).")
            return

        from scenes.game_scene import GameScene

        settings = {
            "algorithm": self.menu_algorithm,
            "dataset": self.menu_dataset,
            "points": self.menu_points,
            "k": self.menu_k,
            "battle_mode": (self.menu_start_mode == "battle"),
            "voronoi": self.menu_voronoi,
            "csv_points": list(self.csv_points),
            "dbscan_eps": self.menu_dbscan_eps,
            "dbscan_min_samples": self.menu_dbscan_min_samples,
            "tutorial": self.menu_tutorial,
        }
        self.app.set_scene(GameScene(self.app, settings))

    def handle_event(self, event):
        items = self._get_items()
        self.menu_index = max(0, min(self.menu_index, len(items) - 1))

        # Mouse selection
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._menu_layout_cache and "rows" in self._menu_layout_cache:
                mx, my = pygame.mouse.get_pos()
                for rect, key in self._menu_layout_cache["rows"]:
                    if rect.collidepoint(mx, my):
                        for i, it in enumerate(items):
                            if it["key"] == key:
                                self.menu_index = i
                                break
                        if key in ("start", "import", "export", "quit"):
                            # activate immediately
                            self.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
                        return
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.app.stop()
            return

        if event.key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % len(items)
            return
        if event.key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % len(items)
            return

        # Shortcuts
        if event.key == pygame.K_5:
            self._apply_item_value("algorithm", "kmeans")
            return
        if event.key == pygame.K_6:
            self._apply_item_value("algorithm", "kmedoids")
            return
        if event.key == pygame.K_7:
            self._apply_item_value("algorithm", "dbscan")
            return
        if event.key == pygame.K_b:
            self._apply_item_value("start_mode", "battle" if self.menu_start_mode != "battle" else "single")
            return
        if event.key == pygame.K_v:
            self._apply_item_value("voronoi", not self.menu_voronoi)
            return
        if event.key == pygame.K_t:
            self._apply_item_value("tutorial", not self.menu_tutorial)
            return
        if event.key == pygame.K_1:
            self._apply_item_value("dataset", "blobs")
            return
        if event.key == pygame.K_2:
            self._apply_item_value("dataset", "moons")
            return
        if event.key == pygame.K_3:
            self._apply_item_value("dataset", "circles")
            return
        if event.key == pygame.K_4:
            self._apply_item_value("dataset", "random")
            return
        if event.key == pygame.K_i:
            ok = self._do_import_csv()
            self._set_message("CSV loaded." if ok else "CSV import cancelled/invalid.")
            return
        if event.key == pygame.K_o:
            ok = self._do_export_csv()
            self._set_message("Exported CSV." if ok else "Export cancelled.")
            return

        current = items[self.menu_index]

        if event.key == pygame.K_RETURN:
            if current["type"] == "action":
                if current["key"] == "start":
                    self._start()
                elif current["key"] == "import":
                    ok = self._do_import_csv()
                    self._set_message("CSV loaded." if ok else "CSV import cancelled/invalid.")
                elif current["key"] == "export":
                    ok = self._do_export_csv()
                    self._set_message("Exported CSV." if ok else "Export cancelled.")
                elif current["key"] == "quit":
                    self.app.stop()
            return

        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            delta = -1 if event.key == pygame.K_LEFT else 1
            if current["type"] == "choice":
                choices = [c[0] for c in current["choices"]]
                i = choices.index(current["value"]) if current["value"] in choices else 0
                new_val = choices[(i + delta) % len(choices)]
                self._apply_item_value(current["key"], new_val)
            elif current["type"] == "int":
                step = int(current.get("step", 1))
                new_val = int(current["value"]) + (step * delta)
                new_val = max(int(current.get("min", new_val)), min(int(current.get("max", new_val)), new_val))
                self._apply_item_value(current["key"], new_val)
            elif current["type"] == "bool":
                self._apply_item_value(current["key"], not bool(current["value"]))

    def update(self, dt_ms):
        # No time-based logic needed (message timeout uses ticks during draw)
        return

    def draw(self):
        screen = self.app.screen
        w, h = screen.get_size()
        screen.fill(config.BG_COLOR)

        title = self.app.menu_title_font.render("Clustering Lab", True, config.COLORS[1])
        subtitle = self.app.menu_section_font.render("Choose settings then press ENTER to start", True, config.TEXT_COLOR)
        screen.blit(title, (24, 18))
        screen.blit(subtitle, (24, 62))

        items = self._get_items()
        self.menu_index = max(0, min(self.menu_index, len(items) - 1))

        top_y = 110
        bottom_h = 120
        content_h = h - bottom_h - top_y - 10

        left_w = 420
        left = pygame.Rect(20, top_y, left_w, content_h)
        right = pygame.Rect(left.right + 15, top_y, w - (left.right + 15) - 20, content_h)

        pygame.draw.rect(screen, config.UI_BG, left, border_radius=14)
        pygame.draw.rect(screen, config.COLORS[3 % len(config.COLORS)], left, 2, border_radius=14)
        pygame.draw.rect(screen, config.UI_BG, right, border_radius=14)
        pygame.draw.rect(screen, config.COLORS[2 % len(config.COLORS)], right, 2, border_radius=14)

        s_title = self.app.menu_section_font.render("Settings", True, config.TEXT_COLOR)
        screen.blit(s_title, (left.x + 16, left.y + 12))

        # Auto-fit rows so the menu always fits all items (no clipping)
        row_start_y = left.y + 52
        gap = 6
        # Leave some padding at the bottom of the panel
        row_area_h = max(1, left.bottom - row_start_y - 12)
        # Row height chosen to fit all items; clamp for readability
        row_h = int((row_area_h + gap) / max(1, len(items)) - gap)
        row_h = max(28, min(38, row_h))
        row_y = row_start_y

        row_font = self.app.menu_item_font if row_h >= 34 else self.app.tiny_font
        self._menu_layout_cache = {"rows": []}

        for idx, it in enumerate(items):
            selected = idx == self.menu_index
            row_rect = pygame.Rect(left.x + 10, row_y, left.w - 20, row_h)
            self._menu_layout_cache["rows"].append((row_rect, it["key"]))

            if selected:
                pygame.draw.rect(screen, (70, 90, 130), row_rect, border_radius=10)
                pygame.draw.rect(screen, config.COLORS[1 % len(config.COLORS)], row_rect, 2, border_radius=10)

            label = it["label"]
            value_text = ""
            if it["type"] == "choice":
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

            label_s = row_font.render(label, True, config.TEXT_COLOR if not selected else (255, 255, 255))
            value_s = row_font.render(value_text, True, config.COLORS[1 % len(config.COLORS)] if selected else config.TEXT_COLOR)

            text_y = row_rect.y + max(0, (row_rect.h - label_s.get_height()) // 2)
            screen.blit(label_s, (row_rect.x + 12, text_y))
            screen.blit(value_s, (row_rect.right - value_s.get_width() - 12, text_y))

            row_y += row_h + gap

        p_title = self.app.menu_section_font.render("Preview", True, config.TEXT_COLOR)
        screen.blit(p_title, (right.x + 16, right.y + 12))

        preview_rect = pygame.Rect(right.x + 14, right.y + 50, right.w - 28, right.h - 64)
        pygame.draw.rect(screen, (28, 28, 38), preview_rect, border_radius=12)
        pygame.draw.rect(screen, (70, 70, 95), preview_rect, 2, border_radius=12)

        if self.menu_dataset == "csv" and not self.csv_points:
            msg = self.app.menu_item_font.render("No CSV loaded. Press I or select Import CSV.", True, config.COLORS[0])
            screen.blit(msg, (preview_rect.x + 12, preview_rect.y + 12))
        else:
            xy = self._preview_xy
            if xy:
                xs = [p[0] for p in xy]
                ys = [p[1] for p in xy]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                dx = max_x - min_x if max_x != min_x else 1
                dy = max_y - min_y if max_y != min_y else 1
                for x, y in random.sample(xy, k=min(len(xy), 220)):
                    px = preview_rect.x + 10 + int(((x - min_x) / dx) * (preview_rect.w - 20))
                    py = preview_rect.y + 10 + int(((y - min_y) / dy) * (preview_rect.h - 20))
                    pygame.draw.circle(screen, (180, 180, 195), (px, py), 2)

        # Bottom help
        help_lines = [
            "NAV: [UP/DOWN] Select   [LEFT/RIGHT] Change   [ENTER] Activate   [ESC] Quit",
            "QUICK: [1-4] Dataset   [5-7] Algorithm   [B] Battle   [V] Voronoi   [T] Tutorial   [I/O] CSV",
        ]

        def wrap(font, text, max_w):
            words = text.split(" ")
            out = []
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if font.size(test)[0] <= max_w:
                    cur = test
                else:
                    if cur:
                        out.append(cur)
                    cur = w
            if cur:
                out.append(cur)
            return out

        max_help_w = w - 44
        help_wrapped = []
        for t in help_lines:
            help_wrapped += wrap(self.app.menu_hint_font, t, max_help_w)

        by = h - 92
        for i, t in enumerate(help_wrapped[:4]):
            surf = self.app.menu_hint_font.render(t, True, (180, 180, 195))
            screen.blit(surf, (22, by + i * 22))

        # Message toast
        if self.menu_message and pygame.time.get_ticks() < self.menu_message_until:
            box = pygame.Rect(w - 420, h - 96, 395, 56)
            pygame.draw.rect(screen, (0, 0, 0), box, border_radius=10)
            pygame.draw.rect(screen, config.COLORS[1 % len(config.COLORS)], box, 2, border_radius=10)
            msg = self.app.menu_item_font.render(self.menu_message, True, (255, 255, 255))
            screen.blit(msg, (box.x + 12, box.y + 16))

        pygame.display.flip()


