"""
📄 Tên File: scene_manager.py (Nằm trong src/ui/)
"""
import pygame
import sys

class SceneManager:
    def __init__(self, screen_w=1280, screen_h=720):
        pygame.init()
        self.screen_w, self.screen_h = screen_w, screen_h
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Self-Defeating Dungeon")
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.current_scene = None

    def switch_scene(self, scene_class, *args, **kwargs):
        self.current_scene = scene_class(self, *args, **kwargs)

    def run(self):
        if not self.current_scene: return
        running = True
        while running:
            time_delta = self.clock.tick(self.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.current_scene.process_event(event)
            self.current_scene.update(time_delta)
            self.current_scene.render(self.screen)
            pygame.display.update()
        pygame.quit()
        sys.exit()