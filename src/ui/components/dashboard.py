"""
📄 Tên File: dashboard.py (Nằm trong src/ui/components/)
* Vai trò: Layout L-Shape, điều phối Theme, cụm nút điều khiển, tốc độ và danh sách thuật toán.
"""
import pygame
from src.ui.components.ui_theme import UITheme
from src.ui.components.ui_progressbar import UIProgressBar

class Dashboard:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

        UITheme.init_fonts()

        # --- THIẾT LẬP LAYOUT L-SHAPE ---
        # 1. Thanh Điều khiển Bên Dưới (Bottom Bar) - Mở rộng chiều cao lên 150
        self.bottom_bar_h = 150
        self.bottom_bar_rect = pygame.Rect(20, screen_h - self.bottom_bar_h - 20, screen_w - 40, self.bottom_bar_h)

        # 2. Panel Bên Phải (Right Panel) - Rút ngắn chiều cao để nhường chỗ cho Bottom Bar
        self.right_panel_w = 320
        self.right_panel_rect = pygame.Rect(screen_w - self.right_panel_w - 20, 20, self.right_panel_w, screen_h - self.bottom_bar_h - 60)

        # --- TRẠNG THÁI GAME ---
        self.current_phase = "HERO"
        self.algo_state = "IDLE"

        # --- LINH KIỆN RIGHT PANEL (HERO PHASE) ---
        bar_x = self.right_panel_rect.x + 20
        bar_y_start = self.right_panel_rect.y + 80
        self.ram_bar = UIProgressBar(bar_x, bar_y_start, self.right_panel_w - 40, 15, "RAM (Frontier)")
        self.cpu_bar = UIProgressBar(bar_x, bar_y_start + 60, self.right_panel_w - 40, 15, "CPU (Expanded)")

        # --- LINH KIỆN BOTTOM BAR ---
        ctrl_x = self.bottom_bar_rect.x + 20
        ctrl_y = self.bottom_bar_rect.y + 25

        # 1. Cụm nút Play / Pause (Góc trái ô màu trắng)
        self.btn_main = pygame.Rect(ctrl_x, ctrl_y, 110, 45)
        self.btn_pause = pygame.Rect(ctrl_x + 120, ctrl_y, 110, 45)

        # 2. Tùy chỉnh tốc độ (Ngay dưới nút Play)
        self.speeds = [0.5, 1.0, 2.0, 3.0]
        self.current_speed = 1.0
        self.speed_rects = []
        for i in range(4):
            self.speed_rects.append(pygame.Rect(ctrl_x + i * 57, ctrl_y + 60, 50, 35))

        # 3. Danh sách Thuật toán & Scroll (Chiếm phần diện tích còn lại bên phải)
        self.algorithms = ["BFS", "DFS", "A*", "Greedy", "Dijkstra", "Bellman", "JPS", "IDA*"]
        self.selected_algo = "BFS"
        self.algo_start_idx = 0 # Vị trí cuộn hiện tại

        # Khu vực chứa các nút thuật toán
        self.algo_area_rect = pygame.Rect(ctrl_x + 260, ctrl_y - 5, self.bottom_bar_rect.w - 300, 120)
        # Nút cuộn Trái/Phải
        self.btn_scroll_left = pygame.Rect(self.algo_area_rect.x, self.algo_area_rect.centery - 20, 30, 40)
        self.btn_scroll_right = pygame.Rect(self.algo_area_rect.right - 30, self.algo_area_rect.centery - 20, 30, 40)

        # Kích thước mỗi khối Thuật toán
        self.algo_card_w = 90
        self.algo_card_h = 100
        self.algo_card_gap = 15
        self.max_visible_algos = (self.algo_area_rect.width - 80) // (self.algo_card_w + self.algo_card_gap)

    def set_phase(self, phase_name):
        if phase_name in UITheme.PALETTES:
            self.current_phase = phase_name

    def process_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # 1. Nút Play/Stop & Pause
            if self.btn_main.collidepoint(mouse_pos):
                if self.algo_state == "IDLE":
                    self.algo_state = "RUNNING"
                else:
                    self.algo_state = "IDLE"

            elif self.algo_state != "IDLE" and self.btn_pause.collidepoint(mouse_pos):
                if self.algo_state == "RUNNING":
                    self.algo_state = "PAUSED"
                elif self.algo_state == "PAUSED":
                    self.algo_state = "RUNNING"

            # 2. Chọn Tốc độ
            for i, rect in enumerate(self.speed_rects):
                if rect.collidepoint(mouse_pos):
                    self.current_speed = self.speeds[i]

            # 3. Nút cuộn danh sách thuật toán
            if self.btn_scroll_left.collidepoint(mouse_pos) and self.algo_start_idx > 0:
                self.algo_start_idx -= 1
            elif self.btn_scroll_right.collidepoint(mouse_pos) and self.algo_start_idx < len(self.algorithms) - self.max_visible_algos:
                self.algo_start_idx += 1

            # 4. Bấm chọn Thuật toán
            start_x = self.algo_area_rect.x + 50
            for i in range(self.max_visible_algos):
                idx = self.algo_start_idx + i
                if idx >= len(self.algorithms): break

                card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 10, self.algo_card_w, self.algo_card_h)
                if card_rect.collidepoint(mouse_pos):
                    self.selected_algo = self.algorithms[idx]
                    print(f">>> Đã chọn thuật toán: {self.selected_algo}")

    def update(self, time_delta, game_stats):
        if self.current_phase == "HERO":
            self.ram_bar.update_value(game_stats.get("ram", 0), game_stats.get("ram_max", 100))
            self.cpu_bar.update_value(game_stats.get("cpu", 0), game_stats.get("cpu_max", 500))

    def _draw_glass_panel(self, surface, rect, palette):
        glass = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glass, palette["panel_bg"], glass.get_rect(), border_radius=12)
        pygame.draw.rect(glass, palette["border"], glass.get_rect(), 2, border_radius=12)
        surface.blit(glass, rect.topleft)

    def draw(self, surface):
        palette = UITheme.PALETTES[self.current_phase]

        # VẼ 2 PANEL LƠ LỬNG
        self._draw_glass_panel(surface, self.right_panel_rect, palette)
        self._draw_glass_panel(surface, self.bottom_bar_rect, palette)

        # --- RIGHT PANEL ---
        if self.current_phase == "HERO":
            header_txt = UITheme.FONT_HEADER.render("RUNNER STATS", True, palette["text_header"])
            surface.blit(header_txt, (self.right_panel_rect.x + 20, self.right_panel_rect.y + 20))
            self.ram_bar.draw(surface, palette, UITheme.FONT_SMALL)
            self.cpu_bar.draw(surface, palette, UITheme.FONT_SMALL)
        elif self.current_phase == "BOSS":
            header_txt = UITheme.FONT_HEADER.render("ARCHITECT TOOLS", True, palette["text_header"])
            surface.blit(header_txt, (self.right_panel_rect.x + 20, self.right_panel_rect.y + 20))

        # --- BOTTOM BAR: PLAY/PAUSE ---
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_main, border_radius=8)
        pygame.draw.rect(surface, palette["border"], self.btn_main, 1, border_radius=8)
        main_label = "► PLAY" if self.algo_state == "IDLE" else "■ STOP"
        main_surf = UITheme.FONT_TEXT.render(main_label, True, palette["text_header"])
        surface.blit(main_surf, (self.btn_main.centerx - main_surf.get_width()//2, self.btn_main.centery - main_surf.get_height()//2))

        if self.algo_state != "IDLE":
            pygame.draw.rect(surface, palette["btn_bg"], self.btn_pause, border_radius=8)
            pygame.draw.rect(surface, palette["border"], self.btn_pause, 1, border_radius=8)
            pause_label = "II PAUSE" if self.algo_state == "RUNNING" else "► RESUME"
            pause_surf = UITheme.FONT_TEXT.render(pause_label, True, palette["text_header"])
            surface.blit(pause_surf, (self.btn_pause.centerx - pause_surf.get_width()//2, self.btn_pause.centery - pause_surf.get_height()//2))

        # --- BOTTOM BAR: SPEED CONTROLS ---
        for i, rect in enumerate(self.speed_rects):
            is_active = (self.current_speed == self.speeds[i])
            bg_color = palette["bar_fill"] if is_active else palette["btn_bg"]
            text_color = (255, 255, 255) if is_active else palette["text_normal"]

            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, palette["border"], rect, 1, border_radius=4)

            speed_txt = UITheme.FONT_SMALL.render(f"{self.speeds[i]}x", True, text_color)
            surface.blit(speed_txt, (rect.centerx - speed_txt.get_width()//2, rect.centery - speed_txt.get_height()//2))

        # --- BOTTOM BAR: ALGORITHM SCROLL AREA ---
        # Vẽ nút cuộn Trái/Phải
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_left, border_radius=4)
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_right, border_radius=4)
        left_arr = UITheme.FONT_TEXT.render("<", True, palette["text_normal"])
        right_arr = UITheme.FONT_TEXT.render(">", True, palette["text_normal"])
        surface.blit(left_arr, (self.btn_scroll_left.centerx - left_arr.get_width()//2, self.btn_scroll_left.centery - left_arr.get_height()//2))
        surface.blit(right_arr, (self.btn_scroll_right.centerx - right_arr.get_width()//2, self.btn_scroll_right.centery - right_arr.get_height()//2))

        # Vẽ các card thuật toán
        start_x = self.algo_area_rect.x + 50
        for i in range(self.max_visible_algos):
            idx = self.algo_start_idx + i
            if idx >= len(self.algorithms): break

            algo_name = self.algorithms[idx]
            is_selected = (algo_name == self.selected_algo)

            card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 10, self.algo_card_w, self.algo_card_h)

            # Đổi màu nổi bật nếu được chọn
            card_bg = palette["border"] if is_selected else palette["bar_bg"]
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=8)
            pygame.draw.rect(surface, palette["border"], card_rect, 2, border_radius=8)

            # Vẽ Logo giả lập (Ví dụ: Chữ cái đầu tiên cực lớn)
            logo_txt = UITheme.FONT_HEADER.render(algo_name[0:2], True, palette["text_header"])
            surface.blit(logo_txt, (card_rect.centerx - logo_txt.get_width()//2, card_rect.y + 20))

            # Vẽ Tên thuật toán
            name_txt = UITheme.FONT_SMALL.render(algo_name, True, palette["text_header"] if is_selected else palette["text_normal"])
            surface.blit(name_txt, (card_rect.centerx - name_txt.get_width()//2, card_rect.bottom - 25))