"""
📄 Tên File: menu_scene.py (Nằm trong src/ui/scenes/)
* Vai trò: Xử lý hiệu ứng kép: Nền mờ dần từ 100% -> 40% đồng bộ với 3 nút trồi lên.
"""
import pygame
from src.ui.scenes.base_scene import BaseScene
from src.ui.components.ui_elements import ImageButton
from src.ui.overlays.settings_overlay import SettingsOverlay
from src.ui.scenes.game_scene.main import GameScene

class MenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.settings_overlay = SettingsOverlay(self.manager.screen_w, self.manager.screen_h)
        self.font_btn = pygame.font.SysFont("consolas", 32, bold=True)

        # Khởi tạo hình nền
        try:
            bg_image = pygame.image.load("assets/images/menu_scene_background.png").convert()
            self.bg_image = pygame.transform.scale(bg_image, (self.manager.screen_w, self.manager.screen_h))
            # KHÔNG đặt cố định 102 nữa, khởi đầu ở 255 (100% độ sáng) để nối tiếp từ SplashScene
            self.bg_image.set_alpha(255)
        except Exception as e:
            print(f"⚠️ Lỗi nạp nền Menu: {e}")
            self.bg_image = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
            self.bg_image.fill((20, 20, 20))

        # --- ĐỊNH NGHĨA VỊ TRÍ ĐÍCH THỰC (TARGET Y) ---
        btn_w, btn_h = 450, 110
        btn_image_path = "assets/images/button_background.png"
        cx = self.manager.screen_w // 2
        sy = 220
        gap = 140

        self.target_y_positions = [sy, sy + gap, sy + gap * 2]

        # Các nút xuất phát từ vị trí thấp hơn vị trí gốc 60px
        self.start_offset = 60
        self.btn_start = ImageButton(cx - btn_w//2, sy + self.start_offset, btn_w, btn_h, btn_image_path, "START", self.font_btn)
        self.btn_tutorials = ImageButton(cx - btn_w//2, (sy + gap) + self.start_offset, btn_w, btn_h, btn_image_path, "TUTORIALS", self.font_btn)
        self.btn_settings = ImageButton(cx - btn_w//2, (sy + gap * 2) + self.start_offset, btn_w, btn_h, btn_image_path, "SETTINGS", self.font_btn)

        self.buttons = [self.btn_start, self.btn_tutorials, self.btn_settings]

        # Bộ quản lý hoạt ảnh đồng bộ
        self.intro_timer = 0.0
        self.intro_duration = 1.2  # Thời gian chạy hiệu ứng (1.2 giây như bạn đã chọn)

    def process_event(self, event):
        if self.settings_overlay.is_open:
            self.settings_overlay.process_event(event)
            return
        # Chỉ cho phép bấm khi hoạt ảnh giới thiệu đã chạy xong hoàn toàn
        if self.intro_timer >= self.intro_duration:
            if self.btn_start.is_clicked(event):
                print(">>> START")
                self.manager.switch_scene(GameScene)
            elif self.btn_tutorials.is_clicked(event):
                print(">>> TUTORIALS")
            elif self.btn_settings.is_clicked(event):
                print(">>> SETTINGS")
                self.settings_overlay.is_open = True

    def update(self, time_delta):
        mouse_pos = pygame.mouse.get_pos()

        # Logic xử lý hoạt ảnh đồng bộ
        if self.intro_timer < self.intro_duration:
            self.intro_timer += time_delta
            progress = min(1.0, self.intro_timer / self.intro_duration)

            # Công thức Ease-Out Quad giúp chuyển động mượt mà ở điểm dừng
            smooth_progress = 1 - (1 - progress) * (1 - progress)

            # 1. HIỆU ỨNG 1: 3 nút bay lên chậm dần
            current_offset = self.start_offset * (1 - smooth_progress)
            for idx, btn in enumerate(self.buttons):
                btn.rect.y = self.target_y_positions[idx] + current_offset

            # 2. HIỆU ỨNG 2: Nền mờ dần (Fade-out độ sáng từ 255 xuống 102)
            # Khi smooth_progress = 0 -> alpha = 255
            # Khi smooth_progress = 1 -> alpha = 102 (40%)
            current_alpha = 255 - (255 - 102) * smooth_progress
            self.bg_image.set_alpha(int(current_alpha))

        # Liên tục kiểm tra hover chuột
        for btn in self.buttons:
            btn.check_hover(mouse_pos)

        self.settings_overlay.update(time_delta)

    def render(self, surface):
        # Lớp nền đen tuyệt đối ở dưới cùng để khi ảnh nền giảm alpha sẽ tạo cảm giác tối dần
        surface.fill((0, 0, 0))

        # Vẽ hình nền với độ mờ được cập nhật liên tục từ hàm update
        surface.blit(self.bg_image, (0, 0))

        # Vẽ các nút bấm
        for btn in self.buttons:
            btn.draw(surface)

        self.settings_overlay.render(surface)