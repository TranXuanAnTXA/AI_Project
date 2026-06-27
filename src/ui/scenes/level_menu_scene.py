"""
📄 Tên File: level_menu_scene.py (Nằm trong src/ui/scenes/)
* Cập nhật: Đẩy vị trí lưới chọn Map xuống khu vực nền tối (Dưới 60% màn hình) để lộ cảnh đẹp.
"""
import pygame
from src.ui.scenes.base_scene import BaseScene

class LevelMenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_level = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 24, bold=True)

        # Load Ảnh nền
        try:
            bg_raw = pygame.image.load("assets/images/menu_level_bg.png").convert()
            self.bg_image = pygame.transform.scale(bg_raw, (self.manager.screen_w, self.manager.screen_h))
        except:
            self.bg_image = pygame.Surface((self.manager.screen_w, self.manager.screen_h))
            self.bg_image.fill((10, 20, 25))

        # Load Khung hình vuông (Block)
        try:
            self.block_img = pygame.image.load("assets/images/block_level_background.png").convert_alpha()
            self.block_w, self.block_h = 120, 140 # Kích thước chuẩn hóa
            self.block_img = pygame.transform.scale(self.block_img, (self.block_w, self.block_h))
        except:
            self.block_img = pygame.Surface((120, 140))
            self.block_img.fill((50, 50, 60))

        # Nút Quay lại
        self.btn_back = pygame.Rect(30, 30, 120, 40)

        # Lấy dữ liệu mở khóa
        from src.core.level_manager import LevelManager
        self.lm = LevelManager()
        self.unlocked_level = self.lm.get_unlocked_level()

        # Hiệu ứng Thác đổ (Cascading Fade-in)
        self.scene_timer = 0.0
        self.total_fade_time = 2.0
        self.blocks = self._generate_blocks()

    def _generate_blocks(self):
        """Xếp 7 khối thành 2 hàng (4 trên, 3 dưới) ở khu vực nền tối bên dưới"""
        blocks = []
        cx = self.manager.screen_w // 2

        gap_x = 50  # Khoảng cách ngang giữa các ô
        gap_y = 30  # Khoảng cách dọc giữa 2 hàng

        # [ĐÃ SỬA CHỖ NÀY]: Đẩy tọa độ Y xuống vùng tối (khoảng 58% chiều cao màn hình trở xuống)
        start_y_top = int(self.manager.screen_h * 0.58)
        start_y_bot = start_y_top + self.block_h + gap_y

        # Tính toán điểm bắt đầu X để căn giữa màn hình
        top_row_x = cx - (self.block_w * 2 + gap_x * 1.5)
        bot_row_x = cx - (self.block_w * 1.5 + gap_x)

        for i in range(1, 8):
            if i <= 4:
                x = top_row_x + (i - 1) * (self.block_w + gap_x)
                y = start_y_top
            else:
                x = bot_row_x + (i - 5) * (self.block_w + gap_x)
                y = start_y_bot

            blocks.append({
                "level": i,
                "rect": pygame.Rect(x, y, self.block_w, self.block_h),
                "is_unlocked": i <= self.unlocked_level,
                "fade_delay": (i - 1) * (self.total_fade_time / 7),
                "alpha": 0.0,
                "hover_scale": 1.0
            })
        return blocks

    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click Back
            if self.btn_back.collidepoint(event.pos):
                from src.ui.scenes.menu_scene import MenuScene
                self.manager.switch_scene(MenuScene)
                return

            # Click chọn Level
            for b in self.blocks:
                if b["is_unlocked"] and b["rect"].collidepoint(event.pos):
                    # [ĐÃ SỬA]: Gọi SplashScene thay vì GameScene
                    from src.ui.scenes.splash_scene import SplashScene

                    # 1. Lấy config của đúng cái level mà người chơi vừa bấm
                    level_config = self.lm.get_level_config(b["level"])

                    # 2. Truyền config và id sang SplashScene
                    self.manager.switch_scene(SplashScene, level_info=level_config, level_to_load=b["level"])

    def update(self, time_delta):
        self.scene_timer += time_delta
        mouse_pos = pygame.mouse.get_pos()

        for b in self.blocks:
            # Hiệu ứng Hover Zoom (Nếu đã mở khóa)
            if b["is_unlocked"] and b["rect"].collidepoint(mouse_pos):
                b["hover_scale"] = min(b["hover_scale"] + 2.0 * time_delta, 1.1)
            else:
                b["hover_scale"] = max(b["hover_scale"] - 2.0 * time_delta, 1.0)

            # Hiệu ứng Fade-in chữ số (Chỉ chạy khi đã qua độ trễ fade_delay)
            if b["is_unlocked"] and self.scene_timer > b["fade_delay"]:
                b["alpha"] = min(b["alpha"] + 400 * time_delta, 255)

    def render(self, surface):
        # 1. Vẽ nền
        surface.blit(self.bg_image, (0, 0))

        # 2. Vẽ nút Back
        pygame.draw.rect(surface, (50, 50, 50), self.btn_back, border_radius=5)
        txt_back = self.font_btn.render("BACK", True, (255, 255, 255))
        surface.blit(txt_back, (self.btn_back.x + 25, self.btn_back.y + 10))

        # 3. Vẽ các Block Level
        for b in self.blocks:
            w = int(self.block_w * b["hover_scale"])
            h = int(self.block_h * b["hover_scale"])
            scaled_img = pygame.transform.smoothscale(self.block_img, (w, h))

            img_rect = scaled_img.get_rect(center=b["rect"].center)

            if not b["is_unlocked"]:
                # Nếu chưa mở khóa: Ám đen ảnh đi
                scaled_img.fill((50, 50, 50), special_flags=pygame.BLEND_MULT)

            surface.blit(scaled_img, img_rect.topleft)

            # Vẽ Số Level đè lên (Hiệu ứng Fade in)
            if b["is_unlocked"] and b["alpha"] > 0:
                txt_num = self.font_level.render(str(b["level"]), True, (150, 255, 150))
                txt_num.set_alpha(int(b["alpha"]))
                surface.blit(txt_num, (img_rect.centerx - txt_num.get_width()//2, img_rect.centery - txt_num.get_height()//2 - 10))