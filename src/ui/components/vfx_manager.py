"""
📄 Tên File: vfx_manager.py (Nằm trong src/ui/components/)
"""
import random
import pygame

class VFXManager:
    @staticmethod
    def apply_rewind_glitch(surface):
        """Phủ lớp nhiễu sóng tím và các đường scanline khi tua ngược thời gian."""
        w, h = surface.get_size()
        glitch_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        alpha = random.randint(40, 80)
        glitch_overlay.fill((155, 50, 255, alpha))
        surface.blit(glitch_overlay, (0, 0))

        # Vẽ các đường nhiễu ngang (Scanlines)
        for _ in range(3):
            ry = random.randint(0, h)
            pygame.draw.line(surface, (255, 255, 255, 100), (0, ry), (w, ry), 1)

    @staticmethod
    def get_camera_jitter():
        """Trả về tuple (dx, dy) để rung lắc camera ngẫu nhiên."""
        return random.randint(-4, 4), random.randint(-4, 4)