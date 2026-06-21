"""
📄 Tên File: splash_scene.py (Nằm trong src/ui/scenes/)
* Vai trò: Hiển thị nền 100% độ sáng, chữ LOADING nhấp nháy và nạp dữ liệu.
"""
import pygame
from src.ui.scenes.base_scene import BaseScene
from src.ui.scenes.menu_scene import MenuScene

class SplashScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_info = pygame.font.SysFont("consolas", 26, bold=True)
        self.timer = 0.0
        self.boot_duration = 4.0  # Thời gian hiển thị Splash (2 giây)

        # Tải hình nền hiển thị 100% sắc nét
        try:
            bg_image = pygame.image.load("assets/images/menu_scene_background.png").convert()
            self.bg_image = pygame.transform.scale(bg_image, (self.manager.screen_w, self.manager.screen_h))
            self.bg_image.set_alpha(255)  # 100% Opacity
        except Exception as e:
            print(f"⚠️ Lỗi nạp nền Splash: {e}")
            self.bg_image = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
            self.bg_image.fill((20, 20, 20))

    def process_event(self, event):
        pass

    def update(self, time_delta):
        self.timer += time_delta
        # Hết thời gian chờ, kích hoạt chuyển sang Menu chính
        if self.timer >= self.boot_duration:
            self.manager.switch_scene(MenuScene)

    def render(self, surface):
        surface.fill((0, 0, 0))

        # Vẽ hình nền gốc
        surface.blit(self.bg_image, (0, 0))

        # Hiệu ứng chữ LOADING... nhấp nháy theo thời gian
        if int(self.timer * 4) % 2 == 0:
            text_surf = self.font_info.render("LOADING...", True, (150, 255, 150))
            # Đặt chữ ở góc dưới bên phải màn hình cho cân đối
            text_x = self.manager.screen_w - text_surf.get_width() - 60
            text_y = self.manager.screen_h - text_surf.get_height() - 60
            surface.blit(text_surf, (text_x, text_y))