import pygame

class DebuffComponent:
    def __init__(self, target_entity):
        self.entity = target_entity
        # Lấy tốc độ gốc để sau này khôi phục
        self.original_speed = getattr(target_entity, 'speed', getattr(target_entity, 'patrol_speed', 0.0))

        self.is_rooted = False
        self.root_timer = 0.0

        self.is_slowed = False
        self.slow_timer = 0.0
        self.slow_factor = 2/3 # Còn 2/3 tốc độ (Bị giảm 1/3)

    def apply_root(self, duration: float):
        self.is_rooted = True
        self.root_timer = duration

        # Ngắt lập tức biến "đang di chuyển" nếu là Hero
        if hasattr(self.entity, 'is_moving'):
            self.entity.is_moving = False

    def apply_slow(self, duration: float):
        self.is_slowed = True
        self.slow_timer = duration

    def update(self, time_delta: float, speed_multiplier: float):
        # 1. TRÓI CHÂN (Ưu tiên cao nhất)
        if self.is_rooted:
            self.root_timer -= time_delta * speed_multiplier

            # Ép tốc độ bằng 0
            if hasattr(self.entity, 'speed'):
                self.entity.speed = 0.0
            else:
                self.entity.current_speed = 0.0

            if self.root_timer <= 0:
                self.is_rooted = False

        # 2. LÀM CHẬM
        elif self.is_slowed:
            self.slow_timer -= time_delta * speed_multiplier

            # Giảm tốc
            if hasattr(self.entity, 'speed'):
                self.entity.speed = self.original_speed * self.slow_factor
            else:
                target_spd = self.entity.chase_speed if self.entity.state == "chase" else self.entity.patrol_speed
                self.entity.current_speed = target_spd * self.slow_factor

            if self.slow_timer <= 0:
                self.is_slowed = False

        # 3. BÌNH THƯỜNG (Khôi phục tốc độ)
        if not self.is_rooted and not self.is_slowed:
            if hasattr(self.entity, 'speed'):
                self.entity.speed = self.original_speed
            else:
                target_spd = getattr(self.entity, 'chase_speed', self.original_speed) if getattr(self.entity, 'state', '') == "chase" else self.original_speed
                self.entity.current_speed = target_spd

    def draw_effects(self, surface, offset_x, offset_y):
        """ Vẽ các icon thể hiện trạng thái xấu đè lên Entity """

        # Vẽ mũi tên hướng xuống nếu bị làm chậm
        if self.is_slowed and hasattr(self.entity, 'pixel_pos'):
            # Lấy tọa độ pixel của thực thể, căn lên đỉnh đầu
            cx = int(self.entity.pixel_pos[0]) + offset_x + (self.entity.tile_size // 2)
            cy = int(self.entity.pixel_pos[1]) + offset_y - 12

            # Cấu trúc đỉnh vẽ mũi tên hướng xuống
            points = [
                (cx - 4, cy - 8),
                (cx + 4, cy - 8),
                (cx + 4, cy - 2),
                (cx + 8, cy - 2),
                (cx, cy + 6),      # Đỉnh mũi tên (chỉ xuống)
                (cx - 8, cy - 2),
                (cx - 4, cy - 2)
            ]

            # Vẽ nền mũi tên màu xanh nhạt và viền trắng
            pygame.draw.polygon(surface, (50, 150, 255), points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 1)

        # Với root (trói), vì ta đã ép entity._animate("hurt") nên không cần vẽ thêm icon rườm rà.