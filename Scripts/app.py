import pygame

import config
from scenes.start_scene import StartScene


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Clustering Visualizer (K‑Means / K‑Medoids / DBSCAN)")
        self.clock = pygame.time.Clock()

        # Fonts (shared across scenes)
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)
        self.menu_title_font = pygame.font.Font(None, 54)
        self.menu_section_font = pygame.font.Font(None, 30)
        self.menu_item_font = pygame.font.Font(None, 26)
        self.menu_hint_font = pygame.font.Font(None, 22)

        self.running = True
        self.fps = config.FPS

        # Persisted user-facing settings (Start/Options menu)
        self.user_settings = {
            "resolution": (config.WIDTH, config.HEIGHT),
            "palette": "default",
        }

        self.scene = StartScene(self)

    def set_scene(self, scene):
        self.scene = scene

    def stop(self):
        self.running = False

    def apply_window_settings(self, width: int, height: int) -> None:
        """Apply a new window size and persist it for subsequent scenes."""
        w = int(max(800, min(2400, width)))
        h = int(max(600, min(1600, height)))
        config.WIDTH, config.HEIGHT = w, h
        self.user_settings["resolution"] = (w, h)
        self.screen = pygame.display.set_mode((w, h))

    def apply_palette(self, mode: str) -> None:
        """Apply a palette mode: 'default' or 'colorblind'."""
        m = str(mode).lower()
        self.user_settings["palette"] = "colorblind" if m.startswith("color") else "default"
        config.set_palette(self.user_settings["palette"])

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(config.FPS)
            self.fps = self.clock.get_fps() if self.clock.get_fps() > 0 else config.FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.scene.handle_event(event)

            self.scene.update(dt_ms)
            self.scene.draw()

        pygame.quit()


