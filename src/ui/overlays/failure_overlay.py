"""
📄 Tên File: failure_overlay.py (Nằm trong src/ui/overlays/)
* Vai trò: Hiển thị lỗi Tràn RAM, Hết giờ... và xử lý nút Retry.
"""
import pygame

class FailureOverlay:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_title = pygame.font.SysFont("consolas", 60, bold=True)
        self.font_msg = pygame.font.SysFont("consolas", 24)

        self.is_active = False

        # Các biến dùng cho hoạt ảnh Float-in (Trồi lên và rõ dần)
        self.alpha = 0
        self.y_offset = 60
        self.reason = ""

        # Nút bấm Reboot
        self.btn_retry = pygame.Rect(self.screen_w//2 - 120, self.screen_h//2 + 100, 240, 50)

    def show(self, reason):
        self.is_active = True
        self.alpha = 0
        self.y_offset = 60 # Điểm bắt đầu trồi lên
        self.reason = reason

    def hide(self):
        self.is_active = False

    def update(self, dt):
        if not self.is_active: return

        # Tăng độ mờ (Fade in)
        if self.alpha < 210:
            self.alpha += 300 * dt
            self.alpha = min(self.alpha, 210)

        # Trồi lên (Float up)
        if self.y_offset > 0:
            self.y_offset -= 120 * dt
            self.y_offset = max(self.y_offset, 0)

    def process_event(self, event):
        """Trả về True nếu click vào nút Retry, ngược lại nếu Overlay đang mở thì nuốt event."""
        if not self.is_active:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_retry.collidepoint(event.pos):
                return "RETRY_CLICKED"

        return True # Khóa event! Ngăn không cho click xuyên xuống Dashboard

    def draw(self, surface):
        if not self.is_active: return

        # 1. Nền đỏ cảnh báo che phủ toàn màn hình
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((50, 5, 5, int(self.alpha)))
        surface.blit(overlay, (0, 0))

        # 2. Tiêu đề SYSTEM FAILURE (Kèm y_offset để tạo hiệu ứng float-in)
        title_y = self.screen_h//2 - 120 + int(self.y_offset)
        title = self.font_title.render("SYSTEM FAILURE", True, (255, 60, 60))
        surface.blit(title, (self.screen_w//2 - title.get_width()//2, title_y))

        # 3. Nguyên nhân (Lấy từ PhaseManager)
        msg = self.font_msg.render(self.reason, True, (220, 220, 220))
        surface.blit(msg, (self.screen_w//2 - msg.get_width()//2, title_y + 80))

        # 4. Nút REBOOT (Chỉ hiện khi chữ đã trồi lên xong cho đẹp)
        if self.y_offset == 0:
            pygame.draw.rect(surface, (100, 20, 20), self.btn_retry, border_radius=8)
            pygame.draw.rect(surface, (255, 50, 50), self.btn_retry, 2, border_radius=8)

            btn_txt = self.font_msg.render("REBOOT (TRY AGAIN)", True, (255, 200, 200))
            surface.blit(btn_txt, (self.btn_retry.centerx - btn_txt.get_width()//2, self.btn_retry.centery - btn_txt.get_height()//2))