"""
📄 Tên File: settings_overlay.py
* Vai trò: Quản lý giao diện cài đặt dạng Tab ngang, hỗ trợ Tab GAME lên đầu, tích hợp nút Restart và Quit Game.
"""
import pygame
import os
import json
from src.ui.components.ui_controls import UISlider, UISwitch, UITabGroup

class UIButton:
    """Thành phần nút bấm tùy chỉnh tương thích hoàn hảo với hệ thống UI điều khiển"""
    def __init__(self, x, y, w, h, text, font, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.callback = callback
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.callback is not None:
                self.callback()
                return True
        return False

    def draw(self, surface):
        base_color = (55, 65, 80) if self.is_hovered else (45, 50, 60)
        border_color = (0, 150, 255) if self.is_hovered else (100, 100, 100)

        pygame.draw.rect(surface, base_color, self.rect, border_radius=4)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=4)

        text_surf = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(text_surf, (self.rect.centerx - text_surf.get_width()//2, self.rect.centery - text_surf.get_height()//2))


class SettingsOverlay:
    def __init__(self, screen_w, screen_h, show_game_tab=False, on_restart=None, on_quit=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.is_open = False
        self.data_path = "data/settings.json"
        self.show_game_tab = show_game_tab

        # Cấu hình phông chữ văn bản
        self.font_tab_normal = pygame.font.SysFont("consolas", 22)
        self.font_tab_active = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_item = pygame.font.SysFont("consolas", 22)

        # Khung panel trung tâm
        self.panel_w, self.panel_h = 800, 500
        self.panel_rect = pygame.Rect((screen_w - self.panel_w)//2, (screen_h - self.panel_h)//2, self.panel_w, self.panel_h)

        # Sắp xếp Tab: Đưa tab GAME lên vị trí ĐẦU TIÊN
        tab_names = []
        if self.show_game_tab:
            tab_names.append("GAME")
        tab_names.extend(["AUDIO", "VIDEO", "AI VISUALS", "ACCESSIBILITY"])

        self.tabs = UITabGroup(self.panel_rect.x + 20, self.panel_rect.y + 20, tab_names, self.font_tab_normal, self.font_tab_active)

        # Nút Đóng hình chữ X góc phải
        self.btn_close = pygame.Rect(self.panel_rect.right - 50, self.panel_rect.top + 20, 30, 30)

        # Nạp dữ liệu cấu hình
        settings_data = self.load_settings()

        # Thông số sắp xếp vị trí các linh kiện UI
        content_x = self.panel_rect.x + 50
        content_y_start = self.panel_rect.y + 120
        item_gap = 65
        item_w = self.panel_w - 100

        # Khởi tạo linh kiện Tab 1: GAME (Chứa Switch cấu hình và các Button chức năng)
        game_data = settings_data.get("game", {"show_fps": True, "allow_pause_anytime": True})
        self.game_controls = [
            UISwitch(content_x, content_y_start, item_w, 40, "Show FPS Overlay", self.font_item, game_data["show_fps"]),
            UISwitch(content_x, content_y_start + item_gap, item_w, 40, "Allow Pause Anytime", self.font_item, game_data["allow_pause_anytime"]),
            UIButton(content_x, content_y_start + item_gap * 2, 220, 42, "Restart Game", self.font_item, on_restart),
            UIButton(content_x + 250, content_y_start + item_gap * 2, 220, 42, "Quit Game", self.font_item, on_quit)
        ]

        # Khởi tạo linh kiện Tab 2: Audio
        audio_data = settings_data["audio"]
        self.audio_controls = [
            UISlider(content_x, content_y_start, item_w, 40, "Master Volume", self.font_item, 0, 100, audio_data["master_volume"]),
            UISlider(content_x, content_y_start + item_gap, item_w, 40, "BGM Volume", self.font_item, 0, 100, audio_data["bgm_volume"]),
            UISlider(content_x, content_y_start + item_gap*2, item_w, 40, "SFX Volume", self.font_item, 0, 100, audio_data["sfx_volume"])
        ]

        # Khởi tạo linh kiện Tab 3: Video
        video_data = settings_data["video"]
        self.video_controls = [
            UISwitch(content_x, content_y_start, item_w, 40, "Fullscreen", self.font_item, video_data["fullscreen"]),
            UISwitch(content_x, content_y_start + item_gap, item_w, 40, "CRT Glitch Effect", self.font_item, video_data["crt_glitch_effect"])
        ]

        # Khởi tạo linh kiện Tab 4: AI Visuals
        ai_data = settings_data["ai_visuals"]
        self.ai_controls = [
            UISlider(content_x, content_y_start, item_w, 40, "Simulation Speed", self.font_item, 1, 4, ai_data["simulation_speed"]),
            UISwitch(content_x, content_y_start + item_gap, item_w, 40, "Show Grid Lines", self.font_item, ai_data["show_grid_lines"]),
            UISwitch(content_x, content_y_start + item_gap*2, item_w, 40, "Show Node Weights", self.font_item, ai_data["show_node_weights"]),
            UISwitch(content_x, content_y_start + item_gap*3, item_w, 40, "Show Visited Trail", self.font_item, ai_data["show_visited_trail"])
        ]

        # Khởi tạo linh kiện Tab 5: Accessibility
        access_data = settings_data["accessibility"]
        self.access_controls = [
            UISwitch(content_x, content_y_start, item_w, 40, "Enable Tooltips", self.font_item, access_data["enable_tooltips"]),
            UISwitch(content_x, content_y_start + item_gap, item_w, 40, "Colorblind Mode", self.font_item, access_data["colorblind_mode"])
        ]

    def load_settings(self):
        default_settings = {
            "audio": {"master_volume": 100, "bgm_volume": 80, "sfx_volume": 100},
            "video": {"fullscreen": False, "crt_glitch_effect": True},
            "ai_visuals": {"simulation_speed": 1, "show_grid_lines": True, "show_node_weights": True, "show_visited_trail": True},
            "accessibility": {"enable_tooltips": True, "colorblind_mode": False},
            "game": {"show_fps": True, "allow_pause_anytime": True}
        }

        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.data_path):
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4, ensure_ascii=False)
            return default_settings

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "game" not in data:
                    data["game"] = default_settings["game"]
                return data
        except (json.JSONDecodeError, KeyError):
            return default_settings

    def save_settings(self):
        settings_data = {
            "audio": {
                "master_volume": int(self.audio_controls[0].value),
                "bgm_volume": int(self.audio_controls[1].value),
                "sfx_volume": int(self.audio_controls[2].value)
            },
            "video": {
                "fullscreen": self.video_controls[0].state,
                "crt_glitch_effect": self.video_controls[1].state
            },
            "ai_visuals": {
                "simulation_speed": int(self.ai_controls[0].value),
                "show_grid_lines": self.ai_controls[1].state,
                "show_node_weights": self.ai_controls[2].state,
                "show_visited_trail": self.ai_controls[3].state
            },
            "accessibility": {
                "enable_tooltips": self.access_controls[0].state,
                "colorblind_mode": self.access_controls[1].state
            },
            "game": {
                "show_fps": self.game_controls[0].state,
                "allow_pause_anytime": self.game_controls[1].state
            }
        }

        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=4, ensure_ascii=False)
        print("💾 Đã lưu các thông số cấu hình phần cứng mới!")

    def _get_current_controls(self):
        """Phân phối điều khiển linh hoạt dựa trên thứ tự Tab hiện hữu"""
        idx = self.tabs.active_idx
        if self.show_game_tab:
            if idx == 0: return self.game_controls
            elif idx == 1: return self.audio_controls
            elif idx == 2: return self.video_controls
            elif idx == 3: return self.ai_controls
            elif idx == 4: return self.access_controls
        else:
            if idx == 0: return self.audio_controls
            elif idx == 1: return self.video_controls
            elif idx == 2: return self.ai_controls
            elif idx == 3: return self.access_controls
        return []

    def process_event(self, event):
        if not self.is_open: return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.collidepoint(event.pos):
                self.save_settings()
                self.is_open = False
                return True

        self.tabs.is_clicked(event)

        for control in self._get_current_controls():
            if hasattr(control, 'process_event'):
                control.process_event(event)
            elif hasattr(control, 'is_clicked'):
                control.is_clicked(event)

        return True

    def update(self, time_delta):
        if not self.is_open: return
        mouse_pos = pygame.mouse.get_pos()
        self.tabs.check_hover(mouse_pos)

        for control in self._get_current_controls():
            control.check_hover(mouse_pos)

    def render(self, surface):
        if not self.is_open: return

        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (30, 30, 35), self.panel_rect)
        pygame.draw.rect(surface, (100, 100, 100), self.panel_rect, 2)

        pygame.draw.rect(surface, (200, 50, 50), self.btn_close)
        x_surf = self.font_item.render("X", True, (255, 255, 255))
        surface.blit(x_surf, (self.btn_close.centerx - x_surf.get_width()//2, self.btn_close.centery - x_surf.get_height()//2))

        self.tabs.draw(surface)
        for control in self._get_current_controls():
            control.draw(surface)