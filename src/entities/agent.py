import pygame
import math

class SpriteSheet:
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
    def __init__(self, start_grid_x: int, start_grid_y: int, tile_size: int, sprite_path: str):
        self.tile_size = tile_size
        self.grid_pos = [start_grid_x, start_grid_y]
        self.pixel_pos = [start_grid_x * self.tile_size, start_grid_y * self.tile_size]
        self.speed = 4.0
        self.is_moving = False
        self.path = []
        self.target_grid_pos = None
        self.direction = "right"
        self.current_frame = 0.0
        self.animation_speed = 0.25
        self.animations = self._load_animations(sprite_path)
        self.image = self.animations[self.direction][0]

        # [MỚI]: Callback để kích hoạt hiệu ứng nổ khói từ GameScene (main.py)
        self.teleport_effect_callback = None

        self.is_teleporting = False
        self.teleport_timer = 0.0
        self.teleport_delay = 1.0  # 1 giây gồng năng lượng
        self.pending_teleport_target = None

    def _load_animations(self, sprite_path: str) -> dict:
        sprite_sheet = SpriteSheet(sprite_path)
        sheet_width = sprite_sheet.sheet.get_width()
        sheet_height = sprite_sheet.sheet.get_height()
        frame_w = sheet_width // 8
        frame_h = sheet_height // 4

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

    def reset_movement(self):
        self.is_moving = False
        self.target_grid_pos = None
        self.path = []
        self.current_frame = 0.0

    def update(self, time_delta: float, speed_multiplier: float = 1.0):
        actual_speed = self.speed * speed_multiplier

        # [MỚI]: Nếu đang trong trạng thái gồng năng lượng để dịch chuyển
        if self.is_teleporting:
            # Thời gian gồng cũng tua nhanh theo tốc độ UI
            self.teleport_timer -= time_delta * speed_multiplier
            if self.teleport_timer <= 0:
                # 1. Hết 1 giây -> Thực hiện Snap (Nhảy)
                target_pixel_x = self.pending_teleport_target[0] * self.tile_size
                target_pixel_y = self.pending_teleport_target[1] * self.tile_size

                self.pixel_pos = [target_pixel_x, target_pixel_y]
                self.grid_pos = list(self.pending_teleport_target)

                # 2. Xóa trạng thái để Hero đi tiếp
                self.is_moving = False
                self.is_teleporting = False
                self.target_grid_pos = None

                # 3. Nổ khói tại vị trí MỚI khi đáp xuống
                if self.teleport_effect_callback:
                    self.teleport_effect_callback(self.pending_teleport_target[0], self.pending_teleport_target[1])
            else:
                self._animate(speed_multiplier) # Vẫn phát animation (Hero bước tại chỗ lúc gồng)
            return # Dừng toàn bộ logic di chuyển vật lý khác cho đến khi nhảy xong

        # LOGIC LẤY BƯỚC ĐI MỚI
        if not self.is_moving and self.path:
            next_step = self.path.pop(0)

            target_pixel_x = next_step[0] * self.tile_size
            target_pixel_y = next_step[1] * self.tile_size
            dx = target_pixel_x - self.pixel_pos[0]
            dy = target_pixel_y - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            # [ĐÃ SỬA]: Chuyển sang trạng thái gồng thay vì nhảy ngay lập tức
            if distance > self.tile_size * 1.5:
                # 1. Nổ khói tại vị trí CŨ để báo hiệu đang gồng skill
                if self.teleport_effect_callback:
                    self.teleport_effect_callback(self.grid_pos[0], self.grid_pos[1])

                self.is_teleporting = True
                self.is_moving = True # Bật True để main.py không cắt ngang quá trình
                self.teleport_timer = self.teleport_delay
                self.pending_teleport_target = next_step

                if dx > 0: self.direction = "right"
                elif dx < 0: self.direction = "left"
                elif dy > 0: self.direction = "down"
                elif dy < 0: self.direction = "up"
            else:
                # DI CHUYỂN BÌNH THƯỜNG TRÊN ĐƯỜNG TRỐNG (Logic cũ)
                self.target_grid_pos = next_step
                self.is_moving = True

                if next_step[0] > self.grid_pos[0]: self.direction = "right"
                elif next_step[0] < self.grid_pos[0]: self.direction = "left"
                elif next_step[1] > self.grid_pos[1]: self.direction = "down"
                elif next_step[1] < self.grid_pos[1]: self.direction = "up"

        # LOGIC TRƯỢT MƯỢT MÀ BÌNH THƯỜNG (Giữ nguyên)
        if self.is_moving and not self.is_teleporting and self.target_grid_pos:
            target_pixel_x = self.target_grid_pos[0] * self.tile_size
            target_pixel_y = self.target_grid_pos[1] * self.tile_size

            dx = target_pixel_x - self.pixel_pos[0]
            dy = target_pixel_y - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            if distance < actual_speed:
                self.pixel_pos = [target_pixel_x, target_pixel_y]
                self.grid_pos = list(self.target_grid_pos)
                self.is_moving = False
                self.target_grid_pos = None
            else:
                self.pixel_pos[0] += (dx / distance) * actual_speed
                self.pixel_pos[1] += (dy / distance) * actual_speed

        self._animate(speed_multiplier)

    def _animate(self, speed_multiplier: float):
        current_anim_list = self.animations[self.direction]

        if self.is_moving:
            self.current_frame += self.animation_speed * speed_multiplier
            if self.current_frame >= len(current_anim_list):
                self.current_frame = 0
            self.image = current_anim_list[int(self.current_frame)]
        else:
            self.current_frame = 0
            self.image = current_anim_list[0]

    def draw(self, surface, offset_x=0, offset_y=0):
        # Ép kiểu số nguyên (int) để đồng bộ tuyệt đối với lưới Pixel của Camera
        center_x = int(self.pixel_pos[0]) + offset_x + (self.tile_size // 2)
        center_y = int(self.pixel_pos[1]) + offset_y + (self.tile_size // 2)

        rect = self.image.get_rect(center=(center_x, center_y))
        rect.y -= 8
        surface.blit(self.image, rect)