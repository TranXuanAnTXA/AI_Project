import pygame
import os
from src.ui.components.ui_theme import UITheme

class VSOverlay:
    def __init__(self, scene):
        self.scene = scene
        self.is_active = False
        self.img_cache = {}

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False

    def _find_image_path(self, filename):
        """Hàm thông minh tự động tìm ảnh ở bất cứ đâu trong dự án"""
        for root, dirs, files in os.walk("."):
            if filename in files:
                return os.path.join(root, filename)
        return filename

    def _get_scaled_image(self, filename, size, fallback_color):
        """Tải, scale và lưu đệm hình ảnh (Dùng cho q_red, q_blue, block)"""
        cache_key = f"{filename}_{size}"
        if cache_key in self.img_cache:
            return self.img_cache[cache_key]

        img = None
        path = self._find_image_path(filename)
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
        except Exception:
            pass

        if img:
            scaled = pygame.transform.smoothscale(img, size)
            self.img_cache[cache_key] = scaled
            return scaled

        # Nếu không tìm thấy ảnh -> Tự vẽ một khung màu thay thế
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, fallback_color, surf.get_rect(), border_radius=12)
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2, border_radius=12)
        self.img_cache[cache_key] = surf
        return surf

    def process_event(self, event):
        if not self.is_active: return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            stats = getattr(self.scene, 'vs_stats', None)
            if not stats: return True

            # Bấm chọn AI 1
            if hasattr(self, 'btn_algo_1') and self.btn_algo_1.collidepoint(mouse_pos):
                if stats["hero1"]["status"] == "REACHED":
                    self.scene.phase_manager.confirm_vs_selection(self.scene.dashboard.selected_algo_1)
                    self.hide()
                    return True
            # Bấm chọn AI 2
            if hasattr(self, 'btn_algo_2') and self.btn_algo_2.collidepoint(mouse_pos):
                if stats["hero2"]["status"] == "REACHED":
                    self.scene.phase_manager.confirm_vs_selection(self.scene.dashboard.selected_algo_2)
                    self.hide()
                    return True
        return True

    def draw(self, surface):
        if not self.is_active: return

        # Đọc dữ liệu đã chụp từ main.py
        stats = getattr(self.scene, 'vs_stats', None)
        if not stats: return

        sw, sh = surface.get_width(), surface.get_height()

        # Màn đen mờ bọc lót
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Khung Box chính
        box_w, box_h = 750, 520
        box_x, box_y = (sw - box_w) // 2, (sh - box_h) // 2

        # Vẽ Tiêu đề
        title = UITheme.FONT_HEADER.render("CHIẾN TRƯỜNG SO SÁNH", True, (255, 215, 0))
        surface.blit(title, (box_x + box_w//2 - title.get_width()//2, box_y))

        # ==================== TÍNH MAX STATS (Để chia tỷ lệ biểu đồ) ====================
        # Đảm bảo không bị chia cho 0 bằng cách dùng max(..., 1)
        max_stats = {
            "cpu": max(stats["hero1"]["cpu"], stats["hero2"]["cpu"], 1),
            "ram": max(stats["hero1"]["ram"], stats["hero2"]["ram"], 1),
            "cost": max(stats["hero1"]["cost"], stats["hero2"]["cost"], 1)
        }

        # ==================== VẼ THẺ HERO 1 (Q_RED) ====================
        card_w, card_h = 280, 350
        card1_rect = pygame.Rect(box_x + 60, box_y + 50, card_w, card_h)
        bg_red = self._get_scaled_image("q_red.png", (card_w, card_h), (120, 20, 20))
        surface.blit(bg_red, card1_rect.topleft)

        algo1_name = self.scene.dashboard.selected_algo_1
        self._draw_card_content(surface, card1_rect, algo1_name, stats["hero1"], max_stats)

        # ==================== VẼ THẺ HERO 2 (Q_BLUE) ====================
        card2_rect = pygame.Rect(box_x + box_w - 60 - card_w, box_y + 50, card_w, card_h)
        bg_blue = self._get_scaled_image("q_blue.png", (card_w, card_h), (20, 60, 120))
        surface.blit(bg_blue, card2_rect.topleft)

        algo2_name = self.scene.dashboard.selected_algo_2
        self._draw_card_content(surface, card2_rect, algo2_name, stats["hero2"], max_stats)

        # Vẽ VS ở giữa
        vs_txt = UITheme.FONT_HEADER.render("VS", True, (255, 255, 255))
        surface.blit(vs_txt, (box_x + box_w//2 - vs_txt.get_width()//2, box_y + card_h//2))

        # ==================== VẼ NÚT BLOCK "CHỌN AI" ====================
        btn_w, btn_h = 130, 130
        self.btn_algo_1 = pygame.Rect(card1_rect.centerx - btn_w//2, card1_rect.bottom, btn_w, btn_h)
        self.btn_algo_2 = pygame.Rect(card2_rect.centerx - btn_w//2, card2_rect.bottom, btn_w, btn_h)

        self._draw_block_button(surface, self.btn_algo_1, stats["hero1"]["status"] == "REACHED")
        self._draw_block_button(surface, self.btn_algo_2, stats["hero2"]["status"] == "REACHED")

    def _draw_card_content(self, surface, rect, algo_name, stat_data, max_stats):
        cx = rect.centerx
        cy = rect.y + 35

        # Tên thuật toán
        algo_title = UITheme.FONT_HEADER.render(algo_name, True, (255, 255, 255))
        surface.blit(algo_title, (cx - algo_title.get_width()//2, cy))

        # Trạng thái Thành Công / Thất bại
        status = stat_data["status"]
        status_text = "THÀNH CÔNG" if status == "REACHED" else ("THẤT BẠI" if status in ["FAILED", "DEAD"] else status)
        color_status = (100, 255, 100) if status == "REACHED" else (255, 100, 100)
        c_status = UITheme.FONT_TEXT.render(status_text, True, color_status)
        surface.blit(c_status, (cx - c_status.get_width()//2, cy + 35))

        # Đường gạch ngang phân cách
        pygame.draw.line(surface, (200, 200, 200, 100), (rect.x + 30, cy + 70), (rect.right - 30, cy + 70), 1)

        # ==================== VẼ BIỂU ĐỒ ====================
        bar_start_y = cy + 90
        bar_gap = 55
        bar_width = rect.w - 60
        bar_height = 10
        bar_x = rect.x + 30

        # CPU (Màu Đỏ Nhạt)
        self._draw_stat_bar(surface, bar_x, bar_start_y, bar_width, bar_height,
                            "Trí lực (CPU)", stat_data['cpu'], max_stats['cpu'], (255, 100, 100))
        # RAM (Màu Xanh Dương Nhạt)
        self._draw_stat_bar(surface, bar_x, bar_start_y + bar_gap, bar_width, bar_height,
                            "Nhãn lực (RAM)", stat_data['ram'], max_stats['ram'], (100, 200, 255))
        # Cost (Màu Xanh Lá)
        self._draw_stat_bar(surface, bar_x, bar_start_y + bar_gap * 2, bar_width, bar_height,
                            "Thể lực (Cost)", stat_data['cost'], max_stats['cost'], (100, 255, 100))

    def _draw_stat_bar(self, surface, x, y, max_w, h, label, val, max_val, color):
        """Hàm helper để vẽ từng thanh bar riêng biệt"""
        # Tên chỉ số (Căn trái)
        lbl = UITheme.FONT_SMALL.render(label, True, (230, 230, 230))
        surface.blit(lbl, (x, y))

        # Số liệu cụ thể (Căn phải)
        val_txt = UITheme.FONT_SMALL.render(str(val), True, (255, 255, 255))
        surface.blit(val_txt, (x + max_w - val_txt.get_width(), y))

        # Tính toán chiều dài cột
        bar_y = y + 25
        ratio = val / max_val if max_val > 0 else 0
        fill_w = int(ratio * max_w)

        # Vẽ viền chìm (Màu xám đen)
        pygame.draw.rect(surface, (50, 50, 50), (x, bar_y, max_w, h), border_radius=4)

        # Vẽ cột tiến trình (Màu sáng)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (x, bar_y, fill_w, h), border_radius=4)

    def _draw_block_button(self, surface, rect, is_enabled):
        """Vẽ nút block_level_background với chữ AI ở chính giữa"""
        color = (255, 255, 255) if is_enabled else (100, 100, 100)
        block_img = self._get_scaled_image("block_level_background.png", (rect.w, rect.h), (50, 50, 50))

        if not is_enabled:
            dark_surf = block_img.copy()
            dark_surf.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(dark_surf, rect.topleft)
        else:
            surface.blit(block_img, rect.topleft)

        text = "CHỌN AI" if is_enabled else "ĐÃ CHẾT"
        t_surf = UITheme.FONT_TEXT.render(text, True, color)

        text_y = rect.y + rect.h * 0.38
        surface.blit(t_surf, (rect.centerx - t_surf.get_width()//2, text_y - t_surf.get_height()//2))