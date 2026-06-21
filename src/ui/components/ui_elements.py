"""
📄 Tên File: ui_elements.py (Nằm trong src/ui/components/)
* Vai trò: Kho chứa các linh kiện UI. Hiện tại là nút bấm dựa trên hình ảnh (ImageButton).
"""

import pygame

class ImageButton:
    def __init__(self, x, y, width, height, image_path, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False

        # Load và scale hình ảnh nút
        try:
            self.base_image = pygame.image.load(image_path).convert_alpha()
            self.base_image = pygame.transform.scale(self.base_image, (width, height))
        except Exception as e:
            print(f"⚠️ Không tìm thấy ảnh {image_path}. Dùng khối màu xám thay thế.")
            self.base_image = pygame.Surface((width, height))
            self.base_image.fill((100, 100, 100))

        # Tạo một ảnh sáng hơn dùng khi chuột lướt qua (Hover effect)
        self.hover_image = self.base_image.copy()
        self.hover_image.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_ADD)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

    def draw(self, surface):
        # 1. Vẽ ảnh nền của nút (sáng lên nếu đang hover)
        current_image = self.hover_image if self.is_hovered else self.base_image
        surface.blit(current_image, self.rect)

        # 2. Vẽ chữ lên giữa nút
        text_color = (150, 255, 150) if self.is_hovered else (220, 220, 220)
        text_surf = self.font.render(self.text, True, text_color)

        # Căn giữa chữ vào tâm của rect
        text_x = self.rect.centerx - text_surf.get_width() // 2
        text_y = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))