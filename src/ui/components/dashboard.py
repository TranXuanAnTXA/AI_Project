"""
📄 Tên File: dashboard.py (Nằm trong src/ui/components/)
* Vai trò: Layout L-Shape, điều phối Theme, cụm nút, tốc độ, danh sách thuật toán/Map động và Timer.
"""
import pygame
import math
from src.ui.components.ui_theme import UITheme
from src.ui.components.ui_progressbar import UIProgressBar

class Dashboard:
    def __init__(self, screen_w, screen_h, level_manager):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.level_manager = level_manager

        UITheme.init_fonts()
        self.font_timer = pygame.font.SysFont("consolas", 42, bold=True)

        # --- THIẾT LẬP LAYOUT L-SHAPE ---
        self.bottom_bar_h = 150
        self.bottom_bar_rect = pygame.Rect(20, screen_h - self.bottom_bar_h - 20, screen_w - 40, self.bottom_bar_h)

        self.right_panel_w = 320
        self.right_panel_rect = pygame.Rect(screen_w - self.right_panel_w - 20, 20, self.right_panel_w, screen_h - self.bottom_bar_h - 60)

        # --- TRẠNG THÁI GAME ---
        self.current_phase = "HERO"
        self.algo_state = "IDLE"
        self.current_round = 1

        # --- LINH KIỆN RIGHT PANEL (HERO PHASE) ---
        bar_x = self.right_panel_rect.x + 20
        bar_y_start = self.right_panel_rect.y + 110
        self.ram_bar = UIProgressBar(bar_x, bar_y_start, self.right_panel_w - 40, 15, "RAM (Frontier)")
        self.cpu_bar = UIProgressBar(bar_x, bar_y_start + 60, self.right_panel_w - 40, 15, "CPU (Expanded)")

        # --- LINH KIỆN BOTTOM BAR ---
        ctrl_x = self.bottom_bar_rect.x + 20
        ctrl_y = self.bottom_bar_rect.y + 25

        self.btn_main = pygame.Rect(ctrl_x, ctrl_y, 110, 45)
        self.btn_pause = pygame.Rect(ctrl_x + 120, ctrl_y, 110, 45)

        self.speeds = [0.5, 1.0, 2.0, 3.0]
        self.current_speed = 1.0
        self.speed_rects = []
        for i in range(4):
            self.speed_rects.append(pygame.Rect(ctrl_x + i * 57, ctrl_y + 60, 50, 35))

        # --- DỮ LIỆU ĐỘNG (Sẽ được nạp qua hàm refresh_algorithms) ---
        self.algorithms = []
        self.selected_algo = ""
        self.algo_start_idx = 0

        self.boss_maps = []
        self.selected_map = ""
        self.map_start_idx = 0

        self.traps = []
        self.selected_trap = None
        self.walls_placed = 0
        self.max_walls = 10

        # --- GIAO DIỆN SCROLL CARD ---
        self.algo_area_rect = pygame.Rect(ctrl_x + 260, ctrl_y - 5, self.bottom_bar_rect.w - 300, 120)
        self.btn_scroll_left = pygame.Rect(self.algo_area_rect.x, self.algo_area_rect.centery - 20, 30, 40)
        self.btn_scroll_right = pygame.Rect(self.algo_area_rect.right - 30, self.algo_area_rect.centery - 20, 30, 40)

        self.algo_card_w = 90
        self.algo_card_h = 100
        self.algo_card_gap = 15
        self.max_visible_algos = (self.algo_area_rect.width - 80) // (self.algo_card_w + self.algo_card_gap)

        # Nạp dữ liệu lần đầu
        self.refresh_algorithms()

    def refresh_algorithms(self):
        """Cập nhật lại danh sách Card thuật toán, bản đồ và bẫy khi chuyển Level"""
        # 1. Làm mới thuật toán cho phe Hero
        self.algorithms = self.level_manager.get_unlocked_algorithms()
        if self.selected_algo not in self.algorithms:
            self.selected_algo = self.algorithms[0] if self.algorithms else ""
        self.algo_start_idx = 0

        # 2. Làm mới bản đồ và bẫy rập cho phe Boss
        self.boss_maps = getattr(self.level_manager, "get_current_maps", lambda: [])()
        self.selected_map = self.boss_maps[0]["name"] if self.boss_maps else ""
        self.map_start_idx = 0

        self.traps = getattr(self.level_manager, "get_unlocked_traps", lambda: [])()
        self.selected_trap = self.traps[0] if self.traps else None
        self.walls_placed = 0

    def set_phase(self, phase_name):
        if phase_name in UITheme.PALETTES:
            self.current_phase = phase_name

    def process_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Nút Run/Stop
            if self.btn_main.collidepoint(mouse_pos):
                if self.algo_state == "IDLE":
                    self.algo_state = "RUNNING"
                else:
                    self.algo_state = "IDLE"

            # Nút Pause/Resume
            elif self.algo_state != "IDLE" and self.btn_pause.collidepoint(mouse_pos):
                if self.algo_state == "RUNNING":
                    self.algo_state = "PAUSED"
                elif self.algo_state == "PAUSED":
                    self.algo_state = "RUNNING"

            # Tốc độ
            for i, rect in enumerate(self.speed_rects):
                if rect.collidepoint(mouse_pos):
                    self.current_speed = self.speeds[i]

            # --- TÁCH LUỒNG CLICK CHO HERO & BOSS ---
            if self.current_phase == "HERO":
                # Cuộn Thuật toán
                if self.btn_scroll_left.collidepoint(mouse_pos) and self.algo_start_idx > 0:
                    self.algo_start_idx -= 1
                elif self.btn_scroll_right.collidepoint(mouse_pos) and self.algo_start_idx < len(self.algorithms) - self.max_visible_algos:
                    self.algo_start_idx += 1

                start_x = self.algo_area_rect.x + 50
                for i in range(self.max_visible_algos):
                    idx = self.algo_start_idx + i
                    if idx >= len(self.algorithms): break

                    card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 10, self.algo_card_w, self.algo_card_h)
                    if card_rect.collidepoint(mouse_pos):
                        self.selected_algo = self.algorithms[idx]
                        print(f">>> Đã chọn thuật toán: {self.selected_algo}")

            elif self.current_phase == "BOSS":
                # Cuộn Map
                if self.btn_scroll_left.collidepoint(mouse_pos) and self.map_start_idx > 0:
                    self.map_start_idx -= 1
                elif self.btn_scroll_right.collidepoint(mouse_pos) and self.map_start_idx < len(self.boss_maps) - self.max_visible_algos:
                    self.map_start_idx += 1

                # Click chọn Map
                start_x = self.algo_area_rect.x + 50
                for i in range(self.max_visible_algos):
                    idx = self.map_start_idx + i
                    if idx >= len(self.boss_maps): break

                    card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 10, self.algo_card_w, self.algo_card_h)
                    if card_rect.collidepoint(mouse_pos):
                        self.selected_map = self.boss_maps[idx]["name"]
                        print(f">>> Boss chọn Map: {self.selected_map}")

                # Boss click chọn Trap ở Right Panel
                trap_rect = pygame.Rect(self.right_panel_rect.x + 20, self.right_panel_rect.y + 90, self.right_panel_rect.w - 40, 50)
                if trap_rect.collidepoint(mouse_pos) and self.traps:
                    print(f">>> Đã chọn công cụ: {self.selected_trap}")

    def update(self, time_delta, game_stats):
        if self.current_phase == "HERO":
            self.ram_bar.update_value(game_stats.get("ram", 0), game_stats.get("ram_max", 100))
            self.cpu_bar.update_value(game_stats.get("cpu", 0), game_stats.get("cpu_max", 500))

    def _draw_glass_panel(self, surface, rect, palette):
        glass = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glass, palette["panel_bg"], glass.get_rect(), border_radius=12)
        pygame.draw.rect(glass, palette["border"], glass.get_rect(), 2, border_radius=12)
        surface.blit(glass, rect.topleft)

    def draw(self, surface, current_timer_val=0.0, timer_state="IDLE"):
        palette = UITheme.PALETTES[self.current_phase]
        lvl_cfg = self.level_manager.get_current_config()

        self._draw_glass_panel(surface, self.right_panel_rect, palette)
        self._draw_glass_panel(surface, self.bottom_bar_rect, palette)

        # --- VẼ ĐỒNG HỒ TOP-CENTER ---
        if timer_state in ["PREPARING", "EXECUTING", "MOVING"]:
            timer_str = f"00:{int(current_timer_val):02d}"
            if current_timer_val <= 10.0 and math.sin(pygame.time.get_ticks() / 100) > 0:
                time_color = (255, 50, 50)
            else:
                time_color = (255, 255, 255)

            time_surf = self.font_timer.render(timer_str, True, time_color)
            timer_rect = pygame.Rect((self.screen_w - 180)//2, 20, 180, 60)
            self._draw_glass_panel(surface, timer_rect, palette)
            surface.blit(time_surf, (timer_rect.centerx - time_surf.get_width()//2, timer_rect.centery - time_surf.get_height()//2))

        # --- RIGHT PANEL VÀ THÔNG SỐ ---
        info_txt = UITheme.FONT_SMALL.render(f"LEVEL {self.level_manager.current_level} - ROUND {self.current_round}/{lvl_cfg.get('max_rounds', 3)}", True, palette["text_normal"])
        surface.blit(info_txt, (self.right_panel_rect.x + 20, self.right_panel_rect.y + 20))

        if self.current_phase == "HERO":
            header_txt = UITheme.FONT_HEADER.render("RUNNER STATS", True, palette["text_header"])
            surface.blit(header_txt, (self.right_panel_rect.x + 20, self.right_panel_rect.y + 50))
            self.ram_bar.draw(surface, palette, UITheme.FONT_SMALL)
            self.cpu_bar.draw(surface, palette, UITheme.FONT_SMALL)

        elif self.current_phase == "BOSS":
            header_txt = UITheme.FONT_HEADER.render("ARCHITECT TOOLS", True, palette["text_header"])
            surface.blit(header_txt, (self.right_panel_rect.x + 20, self.right_panel_rect.y + 50))

            # Box đặt Tường/Bẫy
            trap_rect = pygame.Rect(self.right_panel_rect.x + 20, self.right_panel_rect.y + 90, self.right_panel_rect.w - 40, 50)
            pygame.draw.rect(surface, palette["bar_fill"], trap_rect, border_radius=8)
            pygame.draw.rect(surface, palette["border"], trap_rect, 2, border_radius=8)

            trap_name_display = self.selected_trap if self.selected_trap else "TRAP"
            trap_txt = UITheme.FONT_TEXT.render(f"🧱 {trap_name_display} ({self.walls_placed}/{self.max_walls})", True, (255, 255, 255))
            surface.blit(trap_txt, (trap_rect.centerx - trap_txt.get_width()//2, trap_rect.centery - trap_txt.get_height()//2))

            hint_txt = UITheme.FONT_SMALL.render("*Click chuột trái lên Map để đặt", True, palette["text_normal"])
            surface.blit(hint_txt, (self.right_panel_rect.x + 25, trap_rect.bottom + 10))

        # --- BOTTOM BAR NÚT BẤM (GIỮ NGUYÊN) ---
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_main, border_radius=8)
        pygame.draw.rect(surface, palette["border"], self.btn_main, 1, border_radius=8)
        main_label = "► RUN" if self.algo_state == "IDLE" else "■ STOP"
        main_surf = UITheme.FONT_TEXT.render(main_label, True, palette["text_header"])
        surface.blit(main_surf, (self.btn_main.centerx - main_surf.get_width()//2, self.btn_main.centery - main_surf.get_height()//2))

        if self.algo_state != "IDLE":
            pygame.draw.rect(surface, palette["btn_bg"], self.btn_pause, border_radius=8)
            pygame.draw.rect(surface, palette["border"], self.btn_pause, 1, border_radius=8)
            pause_label = "II PAUSE" if self.algo_state == "RUNNING" else "► RESUME"
            pause_surf = UITheme.FONT_TEXT.render(pause_label, True, palette["text_header"])
            surface.blit(pause_surf, (self.btn_pause.centerx - pause_surf.get_width()//2, self.btn_pause.centery - pause_surf.get_height()//2))

        for i, rect in enumerate(self.speed_rects):
            is_active = (self.current_speed == self.speeds[i])
            bg_color = palette["bar_fill"] if is_active else palette["btn_bg"]
            text_color = (255, 255, 255) if is_active else palette["text_normal"]

            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, palette["border"], rect, 1, border_radius=4)

            speed_txt = UITheme.FONT_SMALL.render(f"{self.speeds[i]}x", True, text_color)
            surface.blit(speed_txt, (rect.centerx - speed_txt.get_width()//2, rect.centery - speed_txt.get_height()//2))

        # --- GIAO DIỆN SCROLL CARD (DÙNG CHUNG CHO CẢ HERO VÀ BOSS) ---
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_left, border_radius=4)
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_right, border_radius=4)
        left_arr = UITheme.FONT_TEXT.render("<", True, palette["text_normal"])
        right_arr = UITheme.FONT_TEXT.render(">", True, palette["text_normal"])
        surface.blit(left_arr, (self.btn_scroll_left.centerx - left_arr.get_width()//2, self.btn_scroll_left.centery - left_arr.get_height()//2))
        surface.blit(right_arr, (self.btn_scroll_right.centerx - right_arr.get_width()//2, self.btn_scroll_right.centery - right_arr.get_height()//2))

        start_x = self.algo_area_rect.x + 50

        # Chọn data để render tùy vào Phase
        items_to_draw = self.algorithms if self.current_phase == "HERO" else [m["name"] for m in self.boss_maps]
        current_start_idx = self.algo_start_idx if self.current_phase == "HERO" else self.map_start_idx
        current_selected = self.selected_algo if self.current_phase == "HERO" else self.selected_map

        for i in range(self.max_visible_algos):
            idx = current_start_idx + i
            if idx >= len(items_to_draw): break

            item_name = items_to_draw[idx]
            is_selected = (item_name == current_selected)

            card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 10, self.algo_card_w, self.algo_card_h)

            card_bg = palette["border"] if is_selected else palette["bar_bg"]
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=8)
            pygame.draw.rect(surface, palette["border"], card_rect, 2, border_radius=8)

            logo_str = item_name[0:2] if self.current_phase == "HERO" else "MAP"
            logo_txt = UITheme.FONT_HEADER.render(logo_str, True, palette["text_header"])
            surface.blit(logo_txt, (card_rect.centerx - logo_txt.get_width()//2, card_rect.y + 20))

            display_name = item_name if len(item_name) < 10 else item_name[:8] + ".."
            name_txt = UITheme.FONT_SMALL.render(display_name, True, palette["text_header"] if is_selected else palette["text_normal"])
            surface.blit(name_txt, (card_rect.centerx - name_txt.get_width()//2, card_rect.bottom - 25))