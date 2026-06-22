"""
📄 Tên File: fly_notification.py (Nằm trong src/ui/overlays/)
* Vai trò: Hiển thị nhiệm vụ đầu mỗi Round và đếm ngược 3-2-1.
"""
import pygame

class FlyNotification:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_title = pygame.font.SysFont("consolas", 40, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 24)

        self.is_active = False
        self.state = "IDLE" # Các trạng thái: SLIDE_IN, HOLD, SLIDE_OUT, COUNTDOWN, DONE

        # Tọa độ Y cho hiệu ứng trượt
        self.y_pos = -200
        self.target_y = 50

        self.timer = 0.0
        self.text_lines = []
        self.countdown_val = 3

    def start(self, level, round_num, phase_name, task_desc):
        """Được gọi bởi GameScene khi bắt đầu một Phase mới"""
        self.text_lines = [
            f"LEVEL {level} - ROUND {round_num}",
            f"PHASE: {phase_name.upper()}",
            f"MISSION: {task_desc}"
        ]
        self.is_active = True
        self.state = "SLIDE_IN"
        self.y_pos = -200
        self.timer = 0.0
        self.countdown_val = 3

    def update(self, dt):
        if not self.is_active: return

        speed = 800 * dt # Tốc độ bay

        if self.state == "SLIDE_IN":
            self.y_pos += speed
            if self.y_pos >= self.target_y:
                self.y_pos = self.target_y
                self.state = "HOLD"
                self.timer = 2.5 # Dừng lại cho người chơi đọc trong 2.5s

        elif self.state == "HOLD":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "SLIDE_OUT"

        elif self.state == "SLIDE_OUT":
            self.y_pos -= speed
            if self.y_pos <= -200:
                self.state = "COUNTDOWN" # Bay xong thì bắt đầu đếm ngược
                self.timer = 1.0 # 1 giây cho mỗi nhịp đếm

        elif self.state == "COUNTDOWN":
            self.timer -= dt
            if self.timer <= 0:
                self.countdown_val -= 1
                self.timer = 1.0
                if self.countdown_val < 0: # Đếm tới 0 (START) thì dừng
                    self.state = "DONE"
                    self.is_active = False

    def draw(self, surface, theme_palette):
        if not self.is_active: return

        # 1. Vẽ bảng thông báo trượt (Slide)
        if self.state in ["SLIDE_IN", "HOLD", "SLIDE_OUT"]:
            panel_w = 700
            panel_h = 160
            rect = pygame.Rect((self.screen_w - panel_w)//2, int(self.y_pos), panel_w, panel_h)

            s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            s.fill(theme_palette["panel_bg"])
            pygame.draw.rect(s, theme_palette["border"], s.get_rect(), 2, border_radius=12)
            surface.blit(s, rect.topleft)

            # Render các dòng chữ
            for i, text in enumerate(self.text_lines):
                font = self.font_title if i == 0 else self.font_sub
                color = theme_palette["text_header"] if i == 0 else theme_palette["text_normal"]
                surf = font.render(text, True, color)
                surface.blit(surf, (rect.centerx - surf.get_width()//2, rect.y + 20 + i*40))

        # 2. Vẽ bộ đếm 3-2-1 khổng lồ giữa màn hình
        elif self.state == "COUNTDOWN":
            font_big = pygame.font.SysFont("consolas", 150, bold=True)
            text = str(self.countdown_val) if self.countdown_val > 0 else "START!"
            # Đổi màu xanh neon/đỏ rực tùy theo Phase
            color = theme_palette["bar_fill"]

            surf = font_big.render(text, True, color)

            # Thêm bóng đen mờ cho chữ dễ đọc trên nền map
            shadow = font_big.render(text, True, (0, 0, 0))
            surface.blit(shadow, (self.screen_w//2 - shadow.get_width()//2 + 4, self.screen_h//2 - shadow.get_height()//2 + 4))
            surface.blit(surf, (self.screen_w//2 - surf.get_width()//2, self.screen_h//2 - surf.get_height()//2))