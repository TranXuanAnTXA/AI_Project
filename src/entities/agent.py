"""
📄 Tên File: agent.py (Nằm trong src/entities/)
* Vai trò: Quản lý logic di chuyển, hoạt ảnh (animation) và hiển thị của các nhân vật.
"""

import pygame
import math

class SpriteSheet:
    """Công cụ hỗ trợ cắt ảnh Spritesheet thành từng khung hình (frame)."""
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            print(f"Không thể tải file ảnh: {filename}")
            raise SystemExit(e)

    def get_image(self, frame_x, frame_y, width, height, scale_factor=2):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (frame_x * width, frame_y * height, width, height))

        scaled_size = (int(width * scale_factor), int(height * scale_factor))
        image = pygame.transform.scale(image, scaled_size)
        return image


class Agent:
    """Thực thể đại diện cho Hero hoặc Bóng ma."""

    def __init__(self, start_grid_x: int, start_grid_y: int, tile_size: int, sprite_path: str):
        self.tile_size = tile_size

        # --- TỌA ĐỘ CHUẨN [X, Y] ---
        self.grid_pos = [start_grid_x, start_grid_y]
        self.pixel_pos = [start_grid_x * self.tile_size, start_grid_y * self.tile_size]

        self.speed = 2.0
        self.is_moving = False
        self.path = []
        self.target_grid_pos = None

        self.direction = "right"
        self.current_frame = 0.0
        self.animation_speed = 0.25  # Tăng nhẹ tốc độ để mượt với 8 frame
        self.animations = self._load_animations(sprite_path)

        self.image = self.animations[self.direction][0]

    def _load_animations(self, sprite_path: str) -> dict:
        """Tự động tính toán kích thước khung hình (8 cột, 4 hàng)"""
        sprite_sheet = SpriteSheet(sprite_path)
        sheet_width = sprite_sheet.sheet.get_width()
        sheet_height = sprite_sheet.sheet.get_height()

        # Lấy chiều rộng chia 8, chiều cao chia 4
        frame_w = sheet_width // 8
        frame_h = sheet_height // 4

        # Chạy đủ 8 khung hình cho mỗi hướng
        anim_dict = {
            "down":  [sprite_sheet.get_image(col, 0, frame_w, frame_h) for col in range(8)],
            "left":  [sprite_sheet.get_image(col, 1, frame_w, frame_h) for col in range(8)],
            "right": [sprite_sheet.get_image(col, 2, frame_w, frame_h) for col in range(8)],
            "up":    [sprite_sheet.get_image(col, 3, frame_w, frame_h) for col in range(8)]
        }
        return anim_dict

    def set_path(self, new_path: list[tuple[int, int]]):
        if new_path and len(new_path) > 0:
            self.path = new_path[1:]

    def update(self):
        if not self.is_moving and self.path:
            next_step = self.path.pop(0)
            self.target_grid_pos = next_step
            self.is_moving = True

            if next_step[0] > self.grid_pos[0]: self.direction = "right"
            elif next_step[0] < self.grid_pos[0]: self.direction = "left"
            elif next_step[1] > self.grid_pos[1]: self.direction = "down"
            elif next_step[1] < self.grid_pos[1]: self.direction = "up"

        if self.is_moving and self.target_grid_pos:
            target_pixel_x = self.target_grid_pos[0] * self.tile_size
            target_pixel_y = self.target_grid_pos[1] * self.tile_size

            dx = target_pixel_x - self.pixel_pos[0]
            dy = target_pixel_y - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            if distance < self.speed:
                self.pixel_pos = [target_pixel_x, target_pixel_y]
                self.grid_pos = list(self.target_grid_pos)
                self.is_moving = False
                self.target_grid_pos = None
            else:
                self.pixel_pos[0] += (dx / distance) * self.speed
                self.pixel_pos[1] += (dy / distance) * self.speed

        self._animate()

    def _animate(self):
        current_anim_list = self.animations[self.direction]

        if self.is_moving:
            self.current_frame += self.animation_speed
            if self.current_frame >= len(current_anim_list):
                self.current_frame = 0
            self.image = current_anim_list[int(self.current_frame)]
        else:
            self.current_frame = 0
            self.image = current_anim_list[0]

    def draw(self, surface, offset_x=0, offset_y=0):
        # 1. Tìm tọa độ tâm của ô lưới mà Hero đang đứng
        center_x = self.pixel_pos[0] + offset_x + (self.tile_size // 2)
        center_y = self.pixel_pos[1] + offset_y + (self.tile_size // 2)

        # 2. Căn giữa ảnh vào tâm ô
        rect = self.image.get_rect(center=(center_x, center_y))

        # 3. Vi chỉnh kéo Hero cao lên 8 pixel để chân khớp với mặt gạch
        rect.y -= 8

        surface.blit(self.image, rect)