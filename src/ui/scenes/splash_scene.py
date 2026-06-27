"""
📄 Tên File: splash_scene.py (Nằm trong src/ui/scenes/)
* Cập nhật: Nhận biến `level_to_load` từ Menu và mang nó qua giao cho GameScene.
"""
import pygame
from src.ui.scenes.base_scene import BaseScene

class SplashScene(BaseScene):
    # [ĐÃ SỬA]: Thêm level_to_load vào tham số khởi tạo
    def __init__(self, manager, level_info=None, level_to_load=1):
        super().__init__(manager)
        self.level_info = level_info
        self.level_to_load = level_to_load

        self.font_info = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 60, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 30)

        try:
            bg_image = pygame.image.load("assets/images/menu_scene_background.png").convert()
            self.bg_image = pygame.transform.scale(bg_image, (self.manager.screen_w, self.manager.screen_h))
            self.bg_image.set_alpha(255)
        except Exception as e:
            print(f"⚠️ Lỗi nạp nền Splash: {e}")
            self.bg_image = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
            self.bg_image.fill((20, 20, 20))

        self.timer = 0.0

        if self.level_info is None:
            self.boot_duration = 4.0
            self.alpha = 0
            self.fade_state = "BOOTING"
        else:
            self.alpha = 255
            self.fade_state = "FADE_IN"

    def process_event(self, event):
        if self.level_info is not None:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if self.fade_state in ["FADE_IN", "HOLD"]:
                    self.fade_state = "FADE_OUT"

    def update(self, time_delta):
        if self.level_info is None:
            self.timer += time_delta
            if self.timer >= self.boot_duration:
                from src.ui.scenes.menu_scene import MenuScene
                self.manager.switch_scene(MenuScene)
        else:
            fade_speed = 300 * time_delta

            if self.fade_state == "FADE_IN":
                self.alpha -= fade_speed
                if self.alpha <= 0:
                    self.alpha = 0
                    self.fade_state = "HOLD"
                    self.timer = 2.0

            elif self.fade_state == "HOLD":
                self.timer -= time_delta
                if self.timer <= 0:
                    self.fade_state = "FADE_OUT"

            elif self.fade_state == "FADE_OUT":
                self.alpha += fade_speed
                if self.alpha >= 255:
                    self.alpha = 255
                    # [ĐÃ SỬA]: Gọi GameScene và truyền lại đúng Level mà người chơi chọn
                    from src.ui.scenes.game_scene.main import GameScene
                    self.manager.switch_scene(GameScene, level_to_load=self.level_to_load)

    def render(self, surface):
        surface.fill((0, 0, 0))
        surface.blit(self.bg_image, (0, 0))

        if self.level_info is None:
            if int(self.timer * 4) % 2 == 0:
                text_surf = self.font_info.render("LOADING...", True, (150, 255, 150))
                text_x = self.manager.screen_w - text_surf.get_width() - 60
                text_y = self.manager.screen_h - text_surf.get_height() - 60
                surface.blit(text_surf, (text_x, text_y))
        else:
            dim_surface = pygame.Surface((self.manager.screen_w, self.manager.screen_h), pygame.SRCALPHA)
            dim_surface.fill((0, 0, 0, 160))
            surface.blit(dim_surface, (0, 0))

            title_text = self.level_info.get('name', 'UNKNOWN LEVEL')
            title = self.font_title.render(title_text, True, (255, 255, 255))
            sub = self.font_sub.render(self.level_info.get("desc", ""), True, (200, 200, 200))

            surface.blit(title, (self.manager.screen_w//2 - title.get_width()//2, self.manager.screen_h//2 - 60))
            surface.blit(sub, (self.manager.screen_w//2 - sub.get_width()//2, self.manager.screen_h//2 + 20))

            if self.alpha > 0:
                fade_overlay = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
                fade_overlay.fill((0, 0, 0))
                fade_overlay.set_alpha(int(self.alpha))
                surface.blit(fade_overlay, (0, 0))