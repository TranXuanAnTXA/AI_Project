"""
📄 Tên File: dashboard.py (Nằm trong src/ui/components/)
* Cập nhật: Căn chỉnh lại khoảng cách (Margin) cho các thanh Progress Bar không đè lên đường viền.
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
        if hasattr(UITheme, 'init_ui_assets'):
            UITheme.init_ui_assets()

        self.font_timer = pygame.font.SysFont("consolas", 42, bold=True)

        # --- THIẾT LẬP LAYOUT ---
        self.right_panel_w = 320
        self.right_panel_rect = pygame.Rect(screen_w - self.right_panel_w - 20, 20, self.right_panel_w, screen_h - 40)

        self.bottom_bar_h = 120
        self.bottom_bar_rect = pygame.Rect(20, screen_h - self.bottom_bar_h - 20, screen_w - self.right_panel_w - 60, self.bottom_bar_h)

        total_right_h = self.right_panel_rect.height
        header_h = 110
        gap = 10
        rem_h = total_right_h - header_h - gap
        half_h = rem_h // 2

        self.right_header_rect = pygame.Rect(self.right_panel_rect.x, self.right_panel_rect.y, self.right_panel_w, header_h)
        self.right_top_rect = pygame.Rect(self.right_panel_rect.x, self.right_panel_rect.y + header_h, self.right_panel_w, half_h)
        self.right_bot_rect = pygame.Rect(self.right_panel_rect.x, self.right_panel_rect.y + header_h + half_h + gap, self.right_panel_w, half_h)

        self.current_phase = "HERO"
        self.algo_state = "IDLE"
        self.current_round = 1

        # --- LINH KIỆN RIGHT PANEL ---
        bar_x = self.right_top_rect.x + 20
        # [ĐÃ SỬA]: Đẩy tọa độ bar xuống dưới 45px để dành khoảng trống 20px cho chữ
        bar_y_start = self.right_top_rect.y + 45

        self.ram_bar = UIProgressBar(bar_x, bar_y_start, self.right_panel_w - 40, 15, "Nhãn Lực (Frontier)")
        # Giãn cách giữa các bar cũng được nới rộng ra cho đẹp mắt (cách nhau 65px)
        self.cpu_bar = UIProgressBar(bar_x, bar_y_start + 65, self.right_panel_w - 40, 15, "Trí Lực (Expanded)")
        self.cost_bar = UIProgressBar(bar_x, bar_y_start + 130, self.right_panel_w - 40, 15, "Thể Lực (Stamina)")

        # Tăng khoảng cách từ 85 lên 110 để không bị đè lên chữ AI
        ghost_bar_y = self.right_bot_rect.y + 110
        self.ghost_ram_bar = UIProgressBar(bar_x, ghost_bar_y, self.right_panel_w - 40, 15, "Nhãn Lực (Ghost)")
        self.ghost_cpu_bar = UIProgressBar(bar_x, ghost_bar_y + 65, self.right_panel_w - 40, 15, "Trí Lực (Ghost)")
        self.ghost_cost_bar = UIProgressBar(bar_x, ghost_bar_y + 130, self.right_panel_w - 40, 15, "Thể Lực (Ghost)")

        # --- LINH KIỆN BOTTOM BAR ---
        ctrl_x = self.bottom_bar_rect.x + 20
        ctrl_y = self.bottom_bar_rect.y + 15

        self.btn_main = pygame.Rect(ctrl_x, ctrl_y, 110, 40)
        self.btn_pause = pygame.Rect(ctrl_x + 120, ctrl_y, 110, 40)

        self.speeds = [0.5, 1.0, 2.0, 3.0]
        self.current_speed = 1.0
        self.speed_rects = []
        for i in range(4):
            self.speed_rects.append(pygame.Rect(ctrl_x + i * 57, ctrl_y + 50, 50, 35))

        # --- DỮ LIỆU ĐỘNG & POPUP CATEGORY ---
        self.algo_groups = []
        self.active_group_name = ""
        self.algorithms_in_group = []

        self.selected_algo = ""
        self.algo_start_idx = 0

        self.boss_maps = []
        self.selected_map = ""
        self.map_start_idx = 0

        self.traps = []
        self.selected_trap = None
        self.walls_placed = 0
        self.max_walls = 10

        self.algo_area_rect = pygame.Rect(ctrl_x + 260, self.bottom_bar_rect.y + 10, self.bottom_bar_rect.w - 430, 100)
        self.btn_scroll_left = pygame.Rect(self.algo_area_rect.x, self.algo_area_rect.centery - 20, 30, 40)
        self.btn_scroll_right = pygame.Rect(self.algo_area_rect.right - 30, self.algo_area_rect.centery - 20, 30, 40)

        btn_popup_size = 80 # Kích thước icon bạn đang dùng
        self.btn_popup = pygame.Rect(
            self.bottom_bar_rect.right - btn_popup_size - 20,
            self.bottom_bar_rect.centery - btn_popup_size // 2,
            btn_popup_size,
            btn_popup_size
        )
        self.show_group_popup = False
        self.popup_scroll_idx = 0

        self.algo_card_w = 80
        self.algo_card_h = 80
        self.algo_card_gap = 15
        self.max_visible_algos = (self.algo_area_rect.width - 80) // (self.algo_card_w + self.algo_card_gap)
        if self.max_visible_algos < 1: self.max_visible_algos = 1

        self.refresh_algorithms()

    def refresh_algorithms(self):
        cfg = self.level_manager.get_current_config()
        if "algo_groups" in cfg:
            self.algo_groups = cfg["algo_groups"]
        else:
            self.algo_groups = [{"group_name": "TẤT CẢ", "algos": self.level_manager.get_unlocked_algorithms()}]

        if self.algo_groups:
            self.active_group_name = self.algo_groups[0]["group_name"]
            self.algorithms_in_group = self.algo_groups[0].get("algos", [])
        else:
            self.algorithms_in_group = []

        if self.selected_algo not in self.algorithms_in_group and self.algorithms_in_group:
            self.selected_algo = self.algorithms_in_group[0]

        self.algo_start_idx = 0
        self.show_group_popup = False

        self.boss_maps = getattr(self.level_manager, "get_current_maps", lambda: [])()
        self.selected_map = self.boss_maps[0]["name"] if self.boss_maps else ""
        self.map_start_idx = 0

        self.traps = getattr(self.level_manager, "get_unlocked_traps", lambda: [])()
        self.selected_trap = self.traps[0] if self.traps else None
        self.walls_placed = 0

    def set_phase(self, phase_name):
        if phase_name in UITheme.PALETTES:
            self.current_phase = phase_name
            self.show_group_popup = False

    def process_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if self.show_group_popup and self.current_phase == "HERO":
                popup_rect = pygame.Rect(self.btn_popup.x, self.btn_popup.y - 150, 200, 140)

                if not popup_rect.collidepoint(mouse_pos) and not self.btn_popup.collidepoint(mouse_pos):
                    self.show_group_popup = False

                if popup_rect.collidepoint(mouse_pos):
                    item_h = 35
                    for i in range(min(4, len(self.algo_groups))):
                        idx = self.popup_scroll_idx + i
                        if idx >= len(self.algo_groups): break
                        item_rect = pygame.Rect(popup_rect.x, popup_rect.y + i * item_h, popup_rect.w, item_h)

                        if item_rect.collidepoint(mouse_pos):
                            self.active_group_name = self.algo_groups[idx]["group_name"]
                            self.algorithms_in_group = self.algo_groups[idx].get("algos", [])
                            self.algo_start_idx = 0
                            if self.algorithms_in_group:
                                self.selected_algo = self.algorithms_in_group[0]
                            self.show_group_popup = False
                            return

            if self.current_phase == "HERO" and self.btn_popup.collidepoint(mouse_pos):
                self.show_group_popup = not self.show_group_popup
                return

            if self.btn_main.collidepoint(mouse_pos):
                if self.algo_state == "IDLE": self.algo_state = "RUNNING"
                else: self.algo_state = "IDLE"

            elif self.algo_state != "IDLE" and self.btn_pause.collidepoint(mouse_pos):
                if self.algo_state == "RUNNING": self.algo_state = "PAUSED"
                elif self.algo_state == "PAUSED": self.algo_state = "RUNNING"

            for i, rect in enumerate(self.speed_rects):
                if rect.collidepoint(mouse_pos):
                    self.current_speed = self.speeds[i]

            if self.current_phase == "HERO":
                if self.btn_scroll_left.collidepoint(mouse_pos) and self.algo_start_idx > 0:
                    self.algo_start_idx -= 1
                elif self.btn_scroll_right.collidepoint(mouse_pos) and self.algo_start_idx < len(self.algorithms_in_group) - self.max_visible_algos:
                    self.algo_start_idx += 1

                start_x = self.algo_area_rect.x + 50
                for i in range(self.max_visible_algos):
                    idx = self.algo_start_idx + i
                    if idx >= len(self.algorithms_in_group): break
                    card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 5, self.algo_card_w, self.algo_card_h)
                    if card_rect.collidepoint(mouse_pos):
                        self.selected_algo = self.algorithms_in_group[idx]

            elif self.current_phase == "BOSS":
                if self.btn_scroll_left.collidepoint(mouse_pos) and self.map_start_idx > 0:
                    self.map_start_idx -= 1
                elif self.btn_scroll_right.collidepoint(mouse_pos) and self.map_start_idx < len(self.boss_maps) - self.max_visible_algos:
                    self.map_start_idx += 1

                start_x = self.algo_area_rect.x + 50
                for i in range(self.max_visible_algos):
                    idx = self.map_start_idx + i
                    if idx >= len(self.boss_maps): break
                    card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 5, self.algo_card_w, self.algo_card_h)
                    if card_rect.collidepoint(mouse_pos):
                        self.selected_map = self.boss_maps[idx]["name"]

                # Cập nhật tọa độ click cho Boss tương đương với lúc vẽ ra
                trap_w, trap_h = 80, 105
                trap_rect = pygame.Rect(self.right_top_rect.centerx - trap_w//2, self.right_top_rect.y + 45, trap_w, trap_h)
                if trap_rect.collidepoint(mouse_pos) and self.traps:
                    pass

        if event.type == pygame.MOUSEWHEEL and self.show_group_popup and self.current_phase == "HERO":
            if event.y > 0 and self.popup_scroll_idx > 0:
                self.popup_scroll_idx -= 1
            elif event.y < 0 and self.popup_scroll_idx < len(self.algo_groups) - 4:
                self.popup_scroll_idx += 1

    def update(self, time_delta, game_stats):
        if self.current_phase == "HERO":
            self.ram_bar.update_value(game_stats.get("ram", 0), game_stats.get("ram_max", 100))
            self.cpu_bar.update_value(game_stats.get("cpu", 0), game_stats.get("cpu_max", 500))

            if self.level_manager.current_level >= 2:
                self.cost_bar.update_value(game_stats.get("cost", 0), game_stats.get("cost_max", 100))

        elif self.current_phase == "BOSS":
            # Ghost Hero nhận dữ liệu giống hệt Hero vì adversarial_scene trả về cùng bộ key
            self.ghost_ram_bar.update_value(game_stats.get("ram", 0), game_stats.get("ram_max", 100))
            self.ghost_cpu_bar.update_value(game_stats.get("cpu", 0), game_stats.get("cpu_max", 500))

            if self.level_manager.current_level >= 2:
                self.ghost_cost_bar.update_value(game_stats.get("cost", 0), game_stats.get("cost_max", 100))

    def _draw_glass_panel(self, surface, rect, palette):
        frame_img = getattr(UITheme, 'frame_boss' if self.current_phase == "BOSS" else 'frame_hero', None)
        if frame_img:
            scaled_frame = pygame.transform.smoothscale(frame_img, (rect.width, rect.height))
            surface.blit(scaled_frame, rect.topleft)
        else:
            pygame.draw.rect(surface, palette["border"], rect, 2, border_radius=12)

    def _draw_fading_line(self, surface, x, y, width, color):
        line_surf = pygame.Surface((width, 2), pygame.SRCALPHA)
        center_x = width // 2
        for i in range(width):
            distance = abs(center_x - i)
            alpha = int(255 * (1 - (distance / center_x)))
            alpha = max(0, min(255, alpha))
            r, g, b = color[:3]
            pygame.draw.line(line_surf, (r, g, b, alpha), (i, 0), (i, 1))
        surface.blit(line_surf, (x, y))

    def draw(self, surface, current_timer_val=0.0, timer_state="IDLE"):
        palette = UITheme.PALETTES[self.current_phase]
        lvl_cfg = self.level_manager.get_current_config()

        self._draw_glass_panel(surface, self.right_panel_rect, palette)
        self._draw_glass_panel(surface, self.bottom_bar_rect, palette)

        if timer_state in ["PREPARING", "EXECUTING", "MOVING"]:
            timer_str = f"00:{int(current_timer_val):02d}"
            time_color = (255, 50, 50) if current_timer_val <= 10.0 and math.sin(pygame.time.get_ticks() / 100) > 0 else (255, 255, 255)
            time_surf = self.font_timer.render(timer_str, True, time_color)
            timer_rect = pygame.Rect((self.screen_w - 180)//2, 10, 180, 60)

            glass = pygame.Surface((timer_rect.width, timer_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glass, palette["panel_bg"], glass.get_rect(), border_radius=12)
            pygame.draw.rect(glass, palette["border"], glass.get_rect(), 2, border_radius=12)
            surface.blit(glass, timer_rect.topleft)
            surface.blit(time_surf, (timer_rect.centerx - time_surf.get_width()//2, timer_rect.centery - time_surf.get_height()//2))

        level_name = lvl_cfg.get("name", f"LEVEL {self.level_manager.current_level}")
        info_txt = UITheme.FONT_SMALL.render(f"{level_name} - ROUND {self.current_round}/{lvl_cfg.get('max_rounds', 3)}", True, palette["text_normal"])
        surface.blit(info_txt, (self.right_header_rect.x + 20, self.right_header_rect.y + 15))

        if self.current_phase == "HERO":
            header_title = lvl_cfg.get("desc", "CHỈ SỐ SINH TỒN")
        else:
            header_title = "ARCHITECT TOOLS"

        header_txt = UITheme.FONT_HEADER.render(header_title, True, palette["text_header"])

        max_title_w = self.right_panel_rect.width - 40
        if header_txt.get_width() > max_title_w:
            scale_factor = max_title_w / header_txt.get_width()
            new_w = int(header_txt.get_width() * scale_factor)
            new_h = int(header_txt.get_height() * scale_factor)
            header_txt = pygame.transform.smoothscale(header_txt, (new_w, new_h))

        surface.blit(header_txt, (self.right_header_rect.x + 20, self.right_header_rect.y + 35))

        line_width = self.right_panel_rect.width - 40
        line_x = self.right_panel_rect.x + 20
        self._draw_fading_line(surface, line_x, self.right_header_rect.bottom, line_width, palette["border"])

        if self.current_phase == "HERO":
            self.ram_bar.draw(surface, palette, UITheme.FONT_SMALL)
            self.cpu_bar.draw(surface, palette, UITheme.FONT_SMALL)
            if self.level_manager.current_level >= 2:
                self.cost_bar.draw(surface, palette, UITheme.FONT_SMALL)
            placeholder_txt = UITheme.FONT_SMALL.render("[ Slot Song Song - Khóa ]", True, (100, 110, 120))
            surface.blit(placeholder_txt, (self.right_bot_rect.centerx - placeholder_txt.get_width()//2, self.right_bot_rect.centery - placeholder_txt.get_height()//2))

        elif self.current_phase == "BOSS":
            # ==========================================
            # SLOT 1: VẼ CÔNG CỤ CỦA BOSS (right_top_rect)
            # ==========================================
            trap_w, trap_h = 80, 105
            trap_rect = pygame.Rect(self.right_top_rect.centerx - trap_w//2, self.right_top_rect.y + 45, trap_w, trap_h)

            q_red = getattr(UITheme, 'q_red', None)
            if q_red:
                scaled_red = pygame.transform.smoothscale(q_red, (trap_rect.w, trap_rect.h))
                surface.blit(scaled_red, trap_rect.topleft)
            else:
                pygame.draw.rect(surface, palette["bar_fill"], trap_rect, border_radius=8)
                pygame.draw.rect(surface, palette["border"], trap_rect, 2, border_radius=8)

            icon_w = getattr(UITheme, 'icon_wall', None)
            if icon_w:
                scaled_icon = pygame.transform.smoothscale(icon_w, (40, 40))
                surface.blit(scaled_icon, (trap_rect.centerx - 20, trap_rect.y + 20))
            else:
                trap_txt = UITheme.FONT_TEXT.render("WALL", True, (255, 255, 255))
                surface.blit(trap_txt, (trap_rect.centerx - trap_txt.get_width()//2, trap_rect.y + 30))

            count_txt = UITheme.FONT_TEXT.render(f"{self.walls_placed}/{self.max_walls}", True, (255, 255, 255))
            surface.blit(count_txt, (trap_rect.centerx - count_txt.get_width()//2, trap_rect.bottom - 30))

            hint_txt = UITheme.FONT_SMALL.render("*Click chuột trái lên Map để đặt", True, palette["text_normal"])
            surface.blit(hint_txt, (self.right_top_rect.centerx - hint_txt.get_width()//2, trap_rect.bottom + 10))

            # Đường kẻ mờ phân cách Slot 1 và Slot 2
            self._draw_fading_line(surface, line_x, self.right_top_rect.bottom, line_width, palette["border"])

            # ==========================================
            # SLOT 2: VẼ THÔNG SỐ GHOST HERO (right_bot_rect)
            # ==========================================
            ghost_header = UITheme.FONT_HEADER.render("GHOST HERO INFO", True, (255, 200, 50))
            surface.blit(ghost_header, (self.right_bot_rect.x + 20, self.right_bot_rect.y + 20))

            algo_name = self.selected_algo if self.selected_algo else "Unknown"
            algo_txt = UITheme.FONT_TEXT.render(f"AI: {algo_name}", True, palette["text_normal"])
            surface.blit(algo_txt, (self.right_bot_rect.x + 20, self.right_bot_rect.y + 55))

            # Vẽ thanh chỉ số cho Ghost
            # Lưu ý: Đảm bảo tọa độ Y này không bị đè lên header của Slot 2
            self.ghost_ram_bar.draw(surface, palette, UITheme.FONT_SMALL)
            self.ghost_cpu_bar.draw(surface, palette, UITheme.FONT_SMALL)
            if self.level_manager.current_level >= 2:
                self.ghost_cost_bar.draw(surface, palette, UITheme.FONT_SMALL)


        self._draw_fading_line(surface, line_x, self.right_top_rect.bottom, line_width, palette["border"])

        pygame.draw.rect(surface, palette["btn_bg"], self.btn_main, border_radius=8)
        pygame.draw.rect(surface, palette["border"], self.btn_main, 1, border_radius=8)
        main_label = "> RUN" if self.algo_state == "IDLE" else "O STOP"
        main_surf = UITheme.FONT_TEXT.render(main_label, True, palette["text_header"])
        surface.blit(main_surf, (self.btn_main.centerx - main_surf.get_width()//2, self.btn_main.centery - main_surf.get_height()//2))

        if self.algo_state != "IDLE":
            pygame.draw.rect(surface, palette["btn_bg"], self.btn_pause, border_radius=8)
            pygame.draw.rect(surface, palette["border"], self.btn_pause, 1, border_radius=8)
            pause_label = "|| PAUSE" if self.algo_state == "RUNNING" else "> RESUME"
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

        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_left, border_radius=4)
        pygame.draw.rect(surface, palette["btn_bg"], self.btn_scroll_right, border_radius=4)
        left_arr = UITheme.FONT_TEXT.render("<", True, palette["text_normal"])
        right_arr = UITheme.FONT_TEXT.render(">", True, palette["text_normal"])
        surface.blit(left_arr, (self.btn_scroll_left.centerx - left_arr.get_width()//2, self.btn_scroll_left.centery - left_arr.get_height()//2))
        surface.blit(right_arr, (self.btn_scroll_right.centerx - right_arr.get_width()//2, self.btn_scroll_right.centery - right_arr.get_height()//2))

        start_x = self.algo_area_rect.x + 50
        items_to_draw = self.algorithms_in_group if self.current_phase == "HERO" else [m["name"] for m in self.boss_maps]
        current_start_idx = self.algo_start_idx if self.current_phase == "HERO" else self.map_start_idx
        current_selected = self.selected_algo if self.current_phase == "HERO" else self.selected_map

        for i in range(self.max_visible_algos):
            idx = current_start_idx + i
            if idx >= len(items_to_draw): break
            item_name = items_to_draw[idx]
            is_selected = (item_name == current_selected)

            card_rect = pygame.Rect(start_x + i * (self.algo_card_w + self.algo_card_gap), self.algo_area_rect.y + 5, self.algo_card_w, self.algo_card_h)

            # --- VẼ NỀN THẺ THUẬT TOÁN (DÙNG Q_BLUE) ---
            q_blue = getattr(UITheme, 'q_blue', None)
            if q_blue and self.current_phase == "HERO":
                scaled_blue = pygame.transform.smoothscale(q_blue, (card_rect.w, card_rect.h))
                surface.blit(scaled_blue, card_rect.topleft)

                # Nếu không được chọn, dội một lớp màng đen mờ lên để làm tối thẻ
                if not is_selected:
                    dark_overlay = pygame.Surface((card_rect.w, card_rect.h), pygame.SRCALPHA)
                    dark_overlay.fill((0, 0, 0, 150))
                    surface.blit(dark_overlay, card_rect.topleft)
            else:
                # Fallback như cũ
                card_bg = palette["border"] if is_selected else (20,30,50, 180)
                card_surf = pygame.Surface((card_rect.w, card_rect.h), pygame.SRCALPHA)
                pygame.draw.rect(card_surf, card_bg, card_surf.get_rect(), border_radius=8)
                pygame.draw.rect(card_surf, palette["border"], card_surf.get_rect(), 2, border_radius=8)
                surface.blit(card_surf, card_rect.topleft)

            # Vẽ Logo Chữ nổi lên trên
            logo_str = item_name[0:2] if self.current_phase == "HERO" else "MAP"
            logo_txt = UITheme.FONT_HEADER.render(logo_str, True, palette["text_header"])
            surface.blit(logo_txt, (card_rect.centerx - logo_txt.get_width()//2, card_rect.y + 25))

            display_name = item_name if len(item_name) < 10 else item_name[:8] + ".."
            name_txt = UITheme.FONT_SMALL.render(display_name, True, palette["text_header"] if is_selected else palette["text_normal"])
            surface.blit(name_txt, (card_rect.centerx - name_txt.get_width()//2, card_rect.bottom - 25))

        if self.current_phase == "HERO" and self.algo_groups:
            btn_icon = getattr(UITheme, 'button_group_icon', None)
            if btn_icon:
                # Scale icon khớp với kích thước của Rect mới (80x80)
                scaled_icon = pygame.transform.smoothscale(btn_icon, (self.btn_popup.width, self.btn_popup.height))
                surface.blit(scaled_icon, self.btn_popup.topleft)
            else:
                pygame.draw.rect(surface, palette["btn_bg"], self.btn_popup, border_radius=8)
                pygame.draw.rect(surface, palette["border"], self.btn_popup, 2, border_radius=8)
            if self.show_group_popup:
                popup_w, popup_h = 200, 140
                popup_rect = pygame.Rect(self.btn_popup.x, self.btn_popup.y - popup_h - 5, popup_w, popup_h)

                pop_surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
                pygame.draw.rect(pop_surf, (15, 25, 40, 240), pop_surf.get_rect(), border_radius=8)
                pygame.draw.rect(pop_surf, palette["border"], pop_surf.get_rect(), 2, border_radius=8)
                surface.blit(pop_surf, popup_rect.topleft)

                item_h = 35
                for i in range(min(4, len(self.algo_groups))):
                    idx = self.popup_scroll_idx + i
                    if idx >= len(self.algo_groups): break

                    item_rect = pygame.Rect(popup_rect.x, popup_rect.y + i * item_h, popup_w, item_h)

                    if self.algo_groups[idx]["group_name"] == self.active_group_name:
                        hl_surf = pygame.Surface((popup_w, item_h), pygame.SRCALPHA)
                        hl_surf.fill((50, 150, 255, 100))
                        surface.blit(hl_surf, item_rect.topleft)

                    if i > 0: pygame.draw.line(surface, palette["border"], (popup_rect.x, item_rect.y), (popup_rect.right, item_rect.y))

                    g_name = self.algo_groups[idx]["group_name"]
                    g_txt = UITheme.FONT_SMALL.render(g_name, True, (255,255,255))
                    surface.blit(g_txt, (item_rect.x + 10, item_rect.centery - g_txt.get_height()//2))