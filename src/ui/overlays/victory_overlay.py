"""
📄 Tên File: victory_overlay.py (Nằm trong src/ui/overlays/)
* Vai trò: Hiển thị thông báo Chiến thắng và cho phép chọn Next Level hoặc Menu.
"""
import pygame

class VictoryOverlay:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_title = pygame.font.SysFont("consolas", 60, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 24, bold=True)

        self.is_active = False
        self.alpha = 0
        self.y_offset = -60 # Hiệu ứng rơi từ trên xuống

        # 2 Nút bấm
        self.btn_next = pygame.Rect(self.screen_w//2 - 260, self.screen_h//2 + 80, 240, 50)
        self.btn_menu = pygame.Rect(self.screen_w//2 + 20, self.screen_h//2 + 80, 240, 50)

    def show(self):
        self.is_active = True
        self.alpha = 0
        self.y_offset = -60

    def hide(self):
        self.is_active = False

    def update(self, dt):
        if not self.is_active: return
        # Mờ dần (Fade-in) nền đen xanh
        if self.alpha < 200:
            self.alpha += 300 * dt
            self.alpha = min(self.alpha, 200)
        # Rơi xuống (Drop-in)
        if self.y_offset < 0:
            self.y_offset += 120 * dt
            self.y_offset = min(self.y_offset, 0)

    def process_event(self, event):
        if not self.is_active: return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_next.collidepoint(event.pos): return "NEXT_LEVEL"
            if self.btn_menu.collidepoint(event.pos): return "LEVEL_MENU"
        return "BLOCK_INPUT" # Chặn click xuyên xuống map

    def draw(self, surface):
        if not self.is_active: return

        # Nền màu lục tối mờ ảo
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((5, 40, 20, int(self.alpha)))
        surface.blit(overlay, (0, 0))

        # Tiêu đề
        title_y = self.screen_h//2 - 100 + int(self.y_offset)
        title = self.font_title.render("LEVEL CLEARED!", True, (100, 255, 150))
        surface.blit(title, (self.screen_w//2 - title.get_width()//2, title_y))

        if self.y_offset == 0:
            # Vẽ nút NEXT LEVEL
            pygame.draw.rect(surface, (20, 100, 50), self.btn_next, border_radius=8)
            pygame.draw.rect(surface, (100, 255, 150), self.btn_next, 2, border_radius=8)
            txt_next = self.font_btn.render("NEXT LEVEL", True, (200, 255, 200))
            surface.blit(txt_next, (self.btn_next.centerx - txt_next.get_width()//2, self.btn_next.centery - txt_next.get_height()//2))

            # Vẽ nút LEVEL MENU
            pygame.draw.rect(surface, (50, 50, 50), self.btn_menu, border_radius=8)
            pygame.draw.rect(surface, (150, 150, 150), self.btn_menu, 2, border_radius=8)
            txt_menu = self.font_btn.render("LEVEL MENU", True, (220, 220, 220))
            surface.blit(txt_menu, (self.btn_menu.centerx - txt_menu.get_width()//2, self.btn_menu.centery - txt_menu.get_height()//2))