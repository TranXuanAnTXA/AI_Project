"""
📄 Tên File: ui_theme.py (Nằm trong src/ui/components/)
* Vai trò: Kho chứa màu sắc, phông chữ và thiết lập giao diện tĩnh. Dễ dàng thay thế assets sau này.
"""
import pygame

class UITheme:
    # Khai báo các biến font ở cấp độ class (tạm thời đặt là None)
    FONT_HEADER = None
    FONT_TEXT = None
    FONT_SMALL = None

    button_group_icon = None


    @classmethod
    def init_fonts(cls):
        # Đường dẫn tới file font vừa copy
        font_regular = "assets/fonts/Roboto-Regular.ttf"
        font_bold = "assets/fonts/Roboto-Bold.ttf"

        try:
            # Sử dụng pygame.font.Font để load thẳng file .ttf
            cls.FONT_HEADER = pygame.font.Font(font_bold, 28)
            cls.FONT_TEXT = pygame.font.Font(font_regular, 18)
            cls.FONT_SMALL = pygame.font.Font(font_regular, 14)
            print("✅ Đã tải thành công bộ font Roboto!")

        except FileNotFoundError:
            # Code phòng hờ (fallback) nếu đường dẫn sai hoặc file bị thiếu
            print("⚠️ Cảnh báo: Không tìm thấy file font Roboto. Đang dùng font dự phòng...")
            cls.FONT_HEADER = pygame.font.SysFont("arial", 28, bold=True)
            cls.FONT_TEXT = pygame.font.SysFont("arial", 18)
            cls.FONT_SMALL = pygame.font.SysFont("arial", 14)


    bg_hero = None
    bg_boss = None
    frame_hero = None
    frame_boss = None

    q_blue = None
    q_red = None
    icon_wall = None


    @classmethod
    def init_ui_assets(cls):
        try:
            # 1. Load và set opacity 50% (128/255) cho nền
            cls.bg_hero = pygame.image.load("assets/images/bg_blue.png").convert_alpha()
            cls.bg_hero.set_alpha(256)  # Opacity 50%

            cls.bg_boss = pygame.image.load("assets/images/bg_red.png").convert_alpha()
            cls.bg_boss.set_alpha(256)  # Opacity 50%

            # 2. Load ảnh viền
            cls.frame_hero = pygame.image.load("assets/images/regtangle_blue.png").convert_alpha()
            cls.frame_boss = pygame.image.load("assets/images/regtangle_red.png").convert_alpha()

            print("✅ Đã load thành công UI Assets (Hình nền & Khung)")
        except Exception as e:
            print(f"⚠️ Lỗi load UI Assets: {e}. Sẽ dùng viền vẽ tay dự phòng.")

        try:
            cls.q_blue = pygame.image.load("assets/images/q_blue.png").convert_alpha()
            cls.q_red = pygame.image.load("assets/images/q_red.png").convert_alpha()
        except Exception as e:
            print(f"⚠️ Lỗi load q_blue/q_red: {e}")

        try:
            cls.icon_wall = pygame.image.load("assets/icons/walls.png").convert_alpha()
        except Exception as e:
            print(f"⚠️ Lỗi load icon_wall: {e}. Sẽ dùng chữ thay thế.")

        try:
            # Thay đổi đường dẫn nếu bạn để ở thư mục khác
            cls.button_group_icon = pygame.image.load("assets/icons/button_group.png").convert_alpha()
        except Exception as e:
            print(f"⚠️ Lỗi load button_group: {e}")

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