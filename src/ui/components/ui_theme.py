"""
📄 Tên File: ui_theme.py (Nằm trong src/ui/components/)
* Vai trò: Kho chứa màu sắc, phông chữ và thiết lập giao diện tĩnh. Dễ dàng thay thế assets sau này.
"""
import pygame

class UITheme:
    # 1. PHÔNG CHỮ (Chỉ khởi tạo khi Pygame đã init)
    @classmethod
    def init_fonts(cls):
        # Header (Tiêu đề): Dùng font sắc nét kiểu Valorant (Tạm dùng Arial/Impact, bạn có thể thay bằng font TTF thật)
        cls.FONT_HEADER = pygame.font.SysFont("impact", 28)
        # Text thông thường (Thông số, Log): Dùng Consolas
        cls.FONT_TEXT = pygame.font.SysFont("consolas", 18)
        cls.FONT_SMALL = pygame.font.SysFont("consolas", 14)

    # 2. CÁC BỘ MÀU THEO PHASE
    PALETTES = {
        "HERO": {
            "panel_bg": (15, 25, 40, 200),       # Xanh dương đen tối (Opacity 200/255 để lơ lửng)
            "border": (50, 150, 255, 150),       # Viền xanh dương sáng
            "text_header": (220, 240, 255),      # Trắng xanh nhạt
            "text_normal": (180, 200, 220),
            "bar_bg": (20, 30, 50),              # Nền progress bar
            "bar_fill": (0, 200, 255),           # Lõi progress bar (Xanh Cyan)
            "btn_bg": (30, 50, 80),
            "btn_hover": (50, 80, 120)
        },
        "BOSS": {
            "panel_bg": (40, 15, 15, 200),       # Đỏ sẫm tối (Opacity 200/255)
            "border": (255, 50, 50, 150),        # Viền đỏ rực
            "text_header": (255, 220, 220),      # Trắng đỏ nhạt
            "text_normal": (220, 180, 180),
            "bar_bg": (50, 20, 20),
            "bar_fill": (220, 20, 40),           # Lõi progress bar (Đỏ máu)
            "btn_bg": (80, 30, 30),
            "btn_hover": (120, 50, 50)
        }
    }