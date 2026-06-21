"""
📄 Tên File: ui_controls.py (Nằm trong src/ui/components/)
* Vai trò: Các linh kiện điều khiển UI (Slider, Switch, Tabs)
"""
import pygame

class UISwitch:
    def __init__(self, x, y, width, height, label, font, initial_state=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        self.state = initial_state
        self.is_hovered = False

        # Khung công tắc nhỏ nằm bên phải
        self.switch_rect = pygame.Rect(x + width - 60, y + height//2 - 15, 60, 30)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.state = not self.state
                return True
        return False

    def draw(self, surface):
        # Vẽ Text (Trắng, nếu hover thì xám nhạt)
        text_color = (200, 255, 200) if self.is_hovered else (255, 255, 255)
        text_surf = self.font.render(self.label, True, text_color)
        surface.blit(text_surf, (self.rect.x, self.rect.centery - text_surf.get_height()//2))

        # Vẽ nền Công tắc
        bg_color = (80, 150, 80) if self.state else (100, 50, 50)
        pygame.draw.rect(surface, bg_color, self.switch_rect, border_radius=15)
        pygame.draw.rect(surface, (200, 200, 200), self.switch_rect, 2, border_radius=15)

        # Vẽ Cục gạt (Knob)
        knob_x = self.switch_rect.right - 26 if self.state else self.switch_rect.left + 4
        knob_rect = pygame.Rect(knob_x, self.switch_rect.y + 4, 22, 22)
        pygame.draw.rect(surface, (220, 220, 220), knob_rect, border_radius=11)


class UISlider:
    def __init__(self, x, y, width, height, label, font, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val

        self.track_rect = pygame.Rect(x + width//2, y + height//2 - 4, width//2, 8)
        self.is_dragging = False
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos) or self.track_rect.collidepoint(mouse_pos)

    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.is_dragging = True
                self._update_value_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self._update_value_from_mouse(event.pos[0])

    def _update_value_from_mouse(self, mouse_x):
        # Tính toán giá trị dựa trên tọa độ X của chuột trên thanh track
        ratio = (mouse_x - self.track_rect.left) / self.track_rect.width
        ratio = max(0.0, min(1.0, ratio)) # Giới hạn từ 0 -> 1
        self.value = self.min_val + ratio * (self.max_val - self.min_val)

    def draw(self, surface):
        # Vẽ Text nhãn
        text_color = (200, 255, 200) if self.is_hovered else (255, 255, 255)
        text_surf = self.font.render(f"{self.label}: {int(self.value)}", True, text_color)
        surface.blit(text_surf, (self.rect.x, self.rect.centery - text_surf.get_height()//2))

        # Vẽ Track (Rãnh trượt)
        pygame.draw.rect(surface, (50, 50, 50), self.track_rect)
        pygame.draw.rect(surface, (100, 100, 100), self.track_rect, 1)

        # Vẽ phần đã Fill (Màu xanh)
        fill_width = int(((self.value - self.min_val) / (self.max_val - self.min_val)) * self.track_rect.width)
        fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_width, self.track_rect.height)
        pygame.draw.rect(surface, (0, 200, 100), fill_rect)

        # Vẽ Knob
        knob_x = self.track_rect.x + fill_width
        knob_rect = pygame.Rect(knob_x - 6, self.track_rect.y - 6, 12, 20)
        pygame.draw.rect(surface, (220, 220, 220), knob_rect)


class UITabGroup:
    def __init__(self, x, y, tabs, font_normal, font_active):
        self.x = x
        self.y = y
        self.tabs = tabs # Danh sách tên tab ["AUDIO", "VIDEO", ...]
        self.font_normal = font_normal
        self.font_active = font_active
        self.active_idx = 0
        self.hover_idx = -1

        self.tab_rects = []
        self._calculate_rects()

    def _calculate_rects(self):
        self.tab_rects = []
        current_x = self.x
        for tab in self.tabs:
            surf = self.font_active.render(tab, True, (255,255,255))
            rect = pygame.Rect(current_x, self.y, surf.get_width() + 40, 50)
            self.tab_rects.append(rect)
            current_x += rect.width

    def check_hover(self, mouse_pos):
        self.hover_idx = -1
        for i, rect in enumerate(self.tab_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_idx = i
                break

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hover_idx != -1:
                self.active_idx = self.hover_idx
                return True
        return False

    def draw(self, surface):
        for i, (tab, rect) in enumerate(zip(self.tabs, self.tab_rects)):
            # Hover hoặc Active thì màu khác, font bự hơn
            is_active = (i == self.active_idx)
            is_hover = (i == self.hover_idx)

            font = self.font_active if is_active else self.font_normal
            color = (255, 255, 255) if is_active else ((200, 255, 200) if is_hover else (150, 150, 150))

            text_surf = font.render(tab, True, color)

            # Căn giữa chữ trong khung Tab
            text_x = rect.centerx - text_surf.get_width() // 2
            text_y = rect.centery - text_surf.get_height() // 2
            surface.blit(text_surf, (text_x, text_y))

            # Nếu Active -> Gạch chân màu vàng
            if is_active:
                pygame.draw.line(surface, (255, 215, 0), (rect.left + 10, rect.bottom), (rect.right - 10, rect.bottom), 4)