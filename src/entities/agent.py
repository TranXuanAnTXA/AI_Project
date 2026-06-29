import pygame
import math
from src.core.game_rules.debuff_manager import DebuffComponent

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
    def __init__(self, start_grid_x: int, start_grid_y: int, tile_size: int, sprite_config):
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

        self.state = "idle"
        self.is_dead = False

        # [MỚI]: Cờ kiểm soát trạng thái trượt băng
        self.is_slipping = False
        self.just_finished_slip = False

        # [MỚI]: Tách bạch logic hồi sinh và lưu vị trí an toàn
        self.last_safe_pos = [start_grid_x, start_grid_y]
        self.is_resurrecting = False
        self.resurrect_timer = 0.0
        self.rollback_pos = None

        self.debuffs = DebuffComponent(self)

        if isinstance(sprite_config, str):
            config = {
                "idle": {"path": sprite_config, "cols": 8},
                "run": {"path": sprite_config, "cols": 8},
                "death": {"path": sprite_config, "cols": 8},
                "hurt": {"path": sprite_config, "cols": 5} # Bổ sung state hurt
            }
        else:
            config = sprite_config

        self.animations = self._load_all_animations(config)
        self.image = self.animations[self.state][self.direction][0]

        self.teleport_effect_callback = None
        self.is_teleporting = False
        self.teleport_timer = 0.0
        self.teleport_delay = 1.0
        self.pending_teleport_target = None

        self.is_ghost = False

    def _load_all_animations(self, config: dict) -> dict:
        all_anims = {}
        for state, details in config.items():
            all_anims[state] = self._load_single_sheet(details["path"], details["cols"])
        return all_anims

    def _load_single_sheet(self, path: str, cols: int) -> dict:
        sprite_sheet = SpriteSheet(path)
        sheet_width = sprite_sheet.sheet.get_width()
        sheet_height = sprite_sheet.sheet.get_height()
        frame_h = sheet_height // 4
        frame_w = frame_h # Ép khung hình vuông để chống cắt lỗi ảnh

        anim_dict = {}
        directions = ["down", "left", "right", "up"]

        for row, direction in enumerate(directions):
            frames = []
            for col in range(cols):
                img = sprite_sheet.get_image(col, row, frame_w, frame_h)
                if img.get_bounding_rect().width > 0:
                    frames.append(img)
            if not frames:
                frames.append(pygame.Surface((frame_w, frame_h), pygame.SRCALPHA))
            anim_dict[direction] = frames

        return anim_dict

    # [MỚI] Hàm reset cứng để dùng khi chuyển Phase 2 hoặc khởi động lại vòng chơi
    def hard_reset(self, start_x: int, start_y: int):
        """Reset toàn bộ trạng thái vật lý khi chuyển Phase mới"""
        self.grid_pos = [start_x, start_y]
        self.pixel_pos = [start_x * self.tile_size, start_y * self.tile_size]
        self.path = []
        self.is_moving = False
        self.target_grid_pos = None
        self.is_slipping = False
        self.is_teleporting = False
        self.is_resurrecting = False
        self.is_dead = False
        self.state = "idle"
        self.direction = "right"
        self.last_safe_pos = [start_x, start_y]
        self.rollback_pos = None
        self.current_frame = 0.0

    def set_path(self, new_path: list[tuple[int, int]]):
        if new_path and len(new_path) > 0 and not self.is_dead and not self.is_resurrecting:
            self.path = new_path[1:]

    def reset_movement(self):
        self.is_moving = False
        self.target_grid_pos = None
        self.path = []
        self.current_frame = 0.0
        self.is_slipping = False
        self.just_finished_slip = False
        if not self.is_dead and not self.is_resurrecting:
            self.state = "idle"

    def die(self):
        self.is_dead = True
        self.state = "death"
        self.current_frame = 0.0
        self.is_moving = False
        self.path = []
        self.is_teleporting = False
        self.is_slipping = False
        self.is_resurrecting = False

    def trigger_slip(self, target_pos):
        self.path = [target_pos]
        self.is_moving = False
        self.target_grid_pos = None
        self.is_slipping = True
        self.just_finished_slip = False
        self.state = "hurt"
        self.is_teleporting = False

        # Xác định hướng văng để xoay mặt Hero
        dx = target_pos[0] - self.grid_pos[0]
        dy = target_pos[1] - self.grid_pos[1]
        if dx > 0: self.direction = "right"
        elif dx < 0: self.direction = "left"
        elif dy > 0: self.direction = "down"
        elif dy < 0: self.direction = "up"

    # [MỚI] Tách hẳn logic Hồi sinh ra khỏi hàm update cũ
    def trigger_resurrect(self, rollback_pos, delay=2.0):
        """Kích hoạt hiệu ứng nằm chết 1 lúc rồi mới dịch chuyển về ô an toàn"""
        self.path = []
        self.is_moving = False
        self.target_grid_pos = None
        self.is_slipping = False
        self.is_teleporting = False # Tắt teleport để không bị giật vị trí

        # Chuyển sang animation ngã gục
        self.state = "death"
        self.current_frame = 0.0

        # Bật cờ hồi sinh
        self.is_resurrecting = True
        self.resurrect_timer = delay
        self.rollback_pos = list(rollback_pos)

    def update(self, time_delta: float, speed_multiplier: float = 1.0):
        if self.is_dead:
            self._animate(speed_multiplier)
            return

        actual_speed = self.speed * speed_multiplier
        self.debuffs.update(time_delta, speed_multiplier)

        # [LOGIC MỚI]: Ưu tiên xử lý Hồi sinh (Chặn mọi hành động khác)
        if self.is_resurrecting:
            self.resurrect_timer -= time_delta * speed_multiplier
            if self.resurrect_timer <= 0:
                self.is_resurrecting = False
                self.state = "idle"
                self.just_finished_slip = True # Báo hiệu cần tính đường mới

                # Dịch chuyển mượt mà về ô an toàn
                if self.rollback_pos:
                    self.grid_pos = list(self.rollback_pos)
                    self.pixel_pos = [self.grid_pos[0] * self.tile_size, self.grid_pos[1] * self.tile_size]
                    self.rollback_pos = None
            else:
                self._animate(speed_multiplier)
            return # Thoát hàm, không chạy logic di chuyển bên dưới

        if self.is_teleporting:
            self.teleport_timer -= time_delta * speed_multiplier
            if self.teleport_timer <= 0:
                target_pixel_x = self.pending_teleport_target[0] * self.tile_size
                target_pixel_y = self.pending_teleport_target[1] * self.tile_size

                self.pixel_pos = [target_pixel_x, target_pixel_y]
                self.grid_pos = list(self.pending_teleport_target)

                self.is_moving = False
                self.is_teleporting = False
                self.target_grid_pos = None

                if self.teleport_effect_callback:
                    self.teleport_effect_callback(self.pending_teleport_target[0], self.pending_teleport_target[1])
            else:
                self._animate(speed_multiplier)
            return

        if not self.is_moving and self.path:
            next_step = self.path.pop(0)

            target_pixel_x = next_step[0] * self.tile_size
            target_pixel_y = next_step[1] * self.tile_size
            dx = target_pixel_x - self.pixel_pos[0]
            dy = target_pixel_y - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            if distance > self.tile_size * 1.5:
                if self.teleport_effect_callback:
                    self.teleport_effect_callback(self.grid_pos[0], self.grid_pos[1])
                self.is_teleporting = True
                self.is_moving = True
                self.teleport_timer = self.teleport_delay
                self.pending_teleport_target = next_step

                # Không cập nhật hướng nếu đang trượt
                if not self.is_slipping:
                    if dx > 0: self.direction = "right"
                    elif dx < 0: self.direction = "left"
                    elif dy > 0: self.direction = "down"
                    elif dy < 0: self.direction = "up"
            else:
                self.target_grid_pos = next_step
                self.is_moving = True

                if not self.is_slipping:
                    if next_step[0] > self.grid_pos[0]: self.direction = "right"
                    elif next_step[0] < self.grid_pos[0]: self.direction = "left"
                    elif next_step[1] > self.grid_pos[1]: self.direction = "down"
                    elif next_step[1] < self.grid_pos[1]: self.direction = "up"

        if self.is_moving and not self.is_teleporting and self.target_grid_pos:
            target_pixel_x = self.target_grid_pos[0] * self.tile_size
            target_pixel_y = self.target_grid_pos[1] * self.tile_size

            dx = target_pixel_x - self.pixel_pos[0]
            dy = target_pixel_y - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            if distance <= actual_speed:
                # [QUAN TRỌNG]: Lưu lại vết chân an toàn TRƯỚC khi nhảy hẳn sang ô mới
                self.last_safe_pos = list(self.grid_pos)

                self.pixel_pos = [target_pixel_x, target_pixel_y]
                self.grid_pos = list(self.target_grid_pos)

                # Ngắt trượt khi tới đích
                if self.is_slipping:
                    self.is_slipping = False
                    self.just_finished_slip = True
                    self.is_moving = False
                    self.target_grid_pos = None
                else:
                    # Logic nối bước mượt mà (Stutter fix)
                    if self.path:
                        next_step = self.path.pop(0)
                        dx_new = (next_step[0] * self.tile_size) - self.pixel_pos[0]
                        dy_new = (next_step[1] * self.tile_size) - self.pixel_pos[1]
                        dist_new = math.hypot(dx_new, dy_new)

                        if dist_new > self.tile_size * 1.5:
                            if self.teleport_effect_callback:
                                self.teleport_effect_callback(self.grid_pos[0], self.grid_pos[1])
                            self.is_teleporting = True
                            self.teleport_timer = self.teleport_delay
                            self.pending_teleport_target = next_step
                        else:
                            self.target_grid_pos = next_step

                        if dx_new > 0: self.direction = "right"
                        elif dx_new < 0: self.direction = "left"
                        elif dy_new > 0: self.direction = "down"
                        elif dy_new < 0: self.direction = "up"
                    else:
                        self.is_moving = False
                        self.target_grid_pos = None
            else:
                self.pixel_pos[0] += (dx / distance) * actual_speed
                self.pixel_pos[1] += (dy / distance) * actual_speed

        # CẬP NHẬT TRẠNG THÁI ANIMATION
        if self.is_slipping:
            self.state = "hurt"
        elif self.is_moving and not self.is_teleporting:
            self.state = "run"
        else:
            self.state = "idle"

        self._animate(speed_multiplier)

    def _animate(self, speed_multiplier: float):
        current_anim_list = self.animations[self.state][self.direction]
        self.current_frame += self.animation_speed * speed_multiplier

        if self.state == "death":
            if self.current_frame >= len(current_anim_list) - 1:
                self.current_frame = len(current_anim_list) - 1
        else:
            if self.current_frame >= len(current_anim_list):
                self.current_frame = 0

        self.image = current_anim_list[int(self.current_frame)]

    def draw(self, surface, offset_x=0, offset_y=0):
        center_x = int(self.pixel_pos[0]) + offset_x + (self.tile_size // 2)
        center_y = int(self.pixel_pos[1]) + offset_y + (self.tile_size // 2)

        rect = self.image.get_rect(center=(center_x, center_y))
        rect.y -= 8

        # [ĐÃ SỬA] Hiệu ứng Bóng ma (Ghost) cho Hero 2
        if self.is_ghost:
            ghost_image = self.image.copy()
            # Cách 1: Làm mờ (Opacity)
            #ghost_image.set_alpha(150)

            # Cách 2: Phủ thêm một lớp màu đỏ nhạt/xanh nhạt để phân biệt (Tùy chọn)
            overlay = pygame.Surface(ghost_image.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 50, 50, 100)) # Phủ màu đỏ mờ
            ghost_image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            surface.blit(ghost_image, rect)
        else:
            surface.blit(self.image, rect)

        self.debuffs.draw_effects(surface, offset_x, offset_y)