"""
📄 Tên File: splash_scene.py (Nằm trong src/ui/scenes/)
* Vai trò: Hiển thị nền lúc khởi động (LOADING) HOẶC làm màn hình chuyển Level (Fade in/out).
"""
import pygame
from src.ui.scenes.base_scene import BaseScene

class SplashScene(BaseScene):
    def __init__(self, manager, level_info=None):
        super().__init__(manager)
        self.level_info = level_info

        # 1. Các Font chữ (Cũ và Mới)
        self.font_info = pygame.font.SysFont("consolas", 26, bold=True) # Dùng cho chữ LOADING
        self.font_title = pygame.font.SysFont("consolas", 60, bold=True) # Dùng cho tên Level
        self.font_sub = pygame.font.SysFont("consolas", 30)              # Dùng cho mô tả Level

        # 2. Tải hình nền hiển thị 100% sắc nét (GIỮ NGUYÊN CODE CŨ CỦA BẠN)
        try:
            bg_image = pygame.image.load("assets/images/menu_scene_background.png").convert()
            self.bg_image = pygame.transform.scale(bg_image, (self.manager.screen_w, self.manager.screen_h))
            self.bg_image.set_alpha(255)  # 100% Opacity
        except Exception as e:
            print(f"⚠️ Lỗi nạp nền Splash: {e}")
            self.bg_image = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
            self.bg_image.fill((20, 20, 20))

        # 3. Setup Trạng thái (Phân nhánh Khởi động vs Chuyển Level)
        self.timer = 0.0

        if self.level_info is None:
            # Chế độ Khởi động Game
            self.boot_duration = 4.0  # Thời gian hiển thị Splash (4 giây)
            self.alpha = 0
            self.fade_state = "BOOTING"
        else:
            # Chế độ Chuyển Level
            self.alpha = 255 # Bắt đầu từ màn hình đen thui
            self.fade_state = "FADE_IN"

    def process_event(self, event):
        # Nếu đang ở màn hình chuyển Level, cho phép click để bỏ qua (Skip) thời gian chờ
        if self.level_info is not None:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if self.fade_state in ["FADE_IN", "HOLD"]:
                    self.fade_state = "FADE_OUT"

    def update(self, time_delta):
        # ==========================================
        # LUỒNG 1: CHẾ ĐỘ SPLASH KHỞI ĐỘNG (CODE CŨ)
        # ==========================================
        if self.level_info is None:
            self.timer += time_delta
            # Hết thời gian chờ, kích hoạt chuyển sang Menu chính
            if self.timer >= self.boot_duration:
                from src.ui.scenes.menu_scene import MenuScene # Import cục bộ tránh lỗi vòng lặp
                self.manager.switch_scene(MenuScene)

        # ==========================================
        # LUỒNG 2: CHẾ ĐỘ CHUYỂN LEVEL (CODE MỚI)
        # ==========================================
        else:
            fade_speed = 300 * time_delta

            if self.fade_state == "FADE_IN":
                self.alpha -= fade_speed
                if self.alpha <= 0:
                    self.alpha = 0
                    self.fade_state = "HOLD"
                    self.timer = 2.0 # Giữ màn hình cho người chơi đọc 2 giây

            elif self.fade_state == "HOLD":
                self.timer -= time_delta
                if self.timer <= 0:
                    self.fade_state = "FADE_OUT"

            elif self.fade_state == "FADE_OUT":
                self.alpha += fade_speed
                if self.alpha >= 255:
                    self.alpha = 255
                    # Đổi cảnh vào thẳng GameScene để chiến đấu Level mới
                    from src.ui.scenes.game_scene import GameScene
                    self.manager.switch_scene(GameScene)

    def render(self, surface):
        surface.fill((0, 0, 0))

        # Luôn vẽ hình nền gốc của bạn
        surface.blit(self.bg_image, (0, 0))

        # ==========================================
        # LUỒNG 1: VẼ CHỮ LOADING NHẤP NHÁY (CODE CŨ)
        # ==========================================
        if self.level_info is None:
            if int(self.timer * 4) % 2 == 0:
                text_surf = self.font_info.render("LOADING...", True, (150, 255, 150))
                # Đặt chữ ở góc dưới bên phải màn hình cho cân đối
                text_x = self.manager.screen_w - text_surf.get_width() - 60
                text_y = self.manager.screen_h - text_surf.get_height() - 60
                surface.blit(text_surf, (text_x, text_y))

        # ==========================================
        # LUỒNG 2: VẼ THÔNG TIN LEVEL VÀ HIỆU ỨNG (MỚI)
        # ==========================================
        else:
            # Phủ một lớp kính mờ lên hình nền để chữ hiển thị rõ ràng hơn
            dim_surface = pygame.Surface((self.manager.screen_w, self.manager.screen_h), pygame.SRCALPHA)
            dim_surface.fill((0, 0, 0, 160)) # Mờ 160/255
            surface.blit(dim_surface, (0, 0))

            # Vẽ chữ Tên Level
            title_text = self.level_info.get('name', 'UNKNOWN LEVEL')
            title = self.font_title.render(title_text, True, (255, 255, 255))
            sub = self.font_sub.render(self.level_info.get("desc", ""), True, (200, 200, 200))

            surface.blit(title, (self.manager.screen_w//2 - title.get_width()//2, self.manager.screen_h//2 - 60))
            surface.blit(sub, (self.manager.screen_w//2 - sub.get_width()//2, self.manager.screen_h//2 + 20))

            # Vẽ lớp bóng tối Fade in/out
            if self.alpha > 0:
                fade_overlay = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
                fade_overlay.fill((0, 0, 0))
                fade_overlay.set_alpha(int(self.alpha))
                surface.blit(fade_overlay, (0, 0))