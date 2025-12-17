import pygame

from config import FPS, HEIGHT, WIDTH
from scenes.menu_scene import MenuScene


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Clustering Visualizer (K-Means / K-Medoids)")
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
        self.fps = FPS

        self.scene = MenuScene(self)

    def set_scene(self, scene):
        self.scene = scene

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            self.fps = self.clock.get_fps() if self.clock.get_fps() > 0 else FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.scene.handle_event(event)

            self.scene.update(dt_ms)
            self.scene.draw()

        pygame.quit()


