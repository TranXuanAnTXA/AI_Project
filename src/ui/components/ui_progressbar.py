"""
📄 Tên File: ui_progressbar.py (Nằm trong src/ui/components/)
"""
import pygame

class UIProgressBar:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.max_value = 100
        self.current_value = 0

    def update_value(self, val, max_val):
        self.current_value = val
        self.max_value = max_val

    def draw(self, surface, theme_palette, font):
        # Vẽ Label
        text_surf = font.render(f"{self.label}: {self.current_value}/{self.max_value}", True, theme_palette["text_normal"])
        surface.blit(text_surf, (self.rect.x, self.rect.y - 20))

        # Vẽ nền Bar
        pygame.draw.rect(surface, theme_palette["bar_bg"], self.rect, border_radius=4)

        # Vẽ lõi Bar
        if self.max_value > 0:
            fill_width = int((self.current_value / self.max_value) * self.rect.width)
            fill_width = max(0, min(fill_width, self.rect.width)) # Kẹp giá trị
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, theme_palette["bar_fill"], fill_rect, border_radius=4)

        # Vẽ viền Bar
        pygame.draw.rect(surface, theme_palette["border"], self.rect, 1, border_radius=4)