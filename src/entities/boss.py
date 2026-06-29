import pygame
import math
import random
from collections import deque
from src.entities.agent import SpriteSheet
from src.core.game_rules.debuff_manager import DebuffComponent

class Boss:
    def __init__(self, start_grid_x: int, start_grid_y: int, tile_size: int, grid_map):
        self.tile_size = tile_size
        self.grid_map = grid_map
        self.grid_pos = [start_grid_x, start_grid_y]
        self.pixel_pos = [start_grid_x * self.tile_size, start_grid_y * self.tile_size]

        self.state = "patrol"
        self.direction = "down"
        self.target_grid_pos = None
        self.path = []

        self.vision_radius = 7
        self.last_seen_hero_pos = None

        self.dfs_visited = set()
        self.dfs_stack = []

        # [ĐÃ SỬA] TỐC ĐỘ VÀNG: Tuần tra 2.0, Truy đuổi 4.8 (Nhanh hơn Hero 20%)
        self.patrol_speed = 2.0
        self.chase_speed = 4.2
        self.current_speed = self.patrol_speed

        self.current_frame = 0.0
        self.animation_speed = 0.2

        self.debuffs = DebuffComponent(self)

        config = {
            "idle": {"path": "assets/sprites/orc3_idle_without_shadow.png", "cols": 4},
            "walk": {"path": "assets/sprites/orc3_walk_without_shadow.png", "cols": 6},
            "run": {"path": "assets/sprites/orc3_run_without_shadow.png", "cols": 6},
            "attack": {"path": "assets/sprites/orc3_run_attack_without_shadow.png", "cols": 6},
            "hurt": {"path": "assets/sprites/orc3_hurt_without_shadow.png", "cols": 6}
        }
        self.animations = self._load_all_animations(config)
        self.image = self.animations["idle"][self.direction][0]

    def _load_all_animations(self, config: dict) -> dict:
        all_anims = {}
        for state, details in config.items():
            all_anims[state] = self._load_single_sheet(details["path"], details["cols"])
        return all_anims

    def _load_single_sheet(self, path: str, cols: int) -> dict:
        sprite_sheet = SpriteSheet(path)
        sheet_height = sprite_sheet.sheet.get_height()
        frame_h = sheet_height // 4
        frame_w = frame_h

        anim_dict = {}
        directions = ["down", "up", "left", "right"]

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

    def get_bfs_path(self, start, goal):
        grid = self.grid_map.grid
        rows, cols = len(grid), len(grid[0])
        queue = deque([(start, [])])
        visited = {start}

        while queue:
            (cx, cy), path = queue.popleft()
            if (cx, cy) == goal:
                return path

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < rows and 0 <= nx < cols:
                    if grid[ny][nx] != 1 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [(nx, ny)]))
        return []

    def get_dfs_patrol_step(self):
        cx, cy = self.grid_pos
        self.dfs_visited.add((cx, cy))

        grid = self.grid_map.grid
        rows, cols = len(grid), len(grid[0])
        valid_neighbors = []

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < rows and 0 <= nx < cols:
                if grid[ny][nx] != 1 and (nx, ny) not in self.dfs_visited:
                    valid_neighbors.append((nx, ny))

        if valid_neighbors:
            next_step = random.choice(valid_neighbors)
            self.dfs_stack.append((cx, cy))
            return [next_step]
        else:
            if self.dfs_stack:
                backtrack_step = self.dfs_stack.pop()
                return [backtrack_step]
            else:
                self.dfs_visited.clear()
                return []

    def think(self, hero_grid_pos):
        dist_to_hero = abs(self.grid_pos[0] - hero_grid_pos[0]) + abs(self.grid_pos[1] - hero_grid_pos[1])

        if dist_to_hero <= self.vision_radius:
            self.state = "chase"
            self.current_speed = self.chase_speed
            self.last_seen_hero_pos = tuple(hero_grid_pos)
            self.path = self.get_bfs_path(tuple(self.grid_pos), self.last_seen_hero_pos)
            self.dfs_stack.clear()
            self.dfs_visited.clear()

        elif getattr(self, 'last_seen_hero_pos', None) is not None:
            if tuple(self.grid_pos) == self.last_seen_hero_pos:
                self.last_seen_hero_pos = None
                self.state = "patrol"
                self.current_speed = self.patrol_speed
                self.path = self.get_dfs_patrol_step()
            else:
                self.state = "chase"
                self.current_speed = self.chase_speed
                self.path = self.get_bfs_path(tuple(self.grid_pos), self.last_seen_hero_pos)
        else:
            self.state = "patrol"
            self.current_speed = self.patrol_speed
            if not self.path:
                self.path = self.get_dfs_patrol_step()

    def update(self, time_delta: float, hero_grid_pos: list, speed_multiplier: float = 1.0):
        self.debuffs.update(time_delta, speed_multiplier)
        actual_speed = self.current_speed * speed_multiplier

        if self.debuffs.is_rooted:
            self._animate("hurt", speed_multiplier)
            return

        if not self.target_grid_pos:
            self.think(hero_grid_pos)
            if self.path:
                self.target_grid_pos = self.path.pop(0)
                dx = self.target_grid_pos[0] - self.grid_pos[0]
                dy = self.target_grid_pos[1] - self.grid_pos[1]
                if dx > 0: self.direction = "right"
                elif dx < 0: self.direction = "left"
                elif dy > 0: self.direction = "down"
                elif dy < 0: self.direction = "up"

        anim_state = "idle"

        if self.target_grid_pos:
            target_px = self.target_grid_pos[0] * self.tile_size
            target_py = self.target_grid_pos[1] * self.tile_size

            dx = target_px - self.pixel_pos[0]
            dy = target_py - self.pixel_pos[1]
            distance = math.hypot(dx, dy)

            anim_state = "run" if self.state == "chase" else "walk"

            dist_to_hero = abs(self.grid_pos[0] - hero_grid_pos[0]) + abs(self.grid_pos[1] - hero_grid_pos[1])
            if self.state == "chase" and dist_to_hero <= 1:
                anim_state = "attack"

            if distance <= actual_speed:
                self.grid_pos = list(self.target_grid_pos)
                self.pixel_pos = [target_px, target_py]

                # [FIX]: BẢO TOÀN ĐỘNG NĂNG (Momentum Carryover)
                # Tính lượng pixel đi dư ra sau khi bước vào giữa ô
                remainder = actual_speed - distance
                self.target_grid_pos = None

                # Lập tức lấy bước tiếp theo và áp dụng số tốc độ dư thừa
                self.think(hero_grid_pos)
                if self.path:
                    self.target_grid_pos = self.path.pop(0)
                    next_px = self.target_grid_pos[0] * self.tile_size
                    next_py = self.target_grid_pos[1] * self.tile_size
                    ndx = next_px - self.pixel_pos[0]
                    ndy = next_py - self.pixel_pos[1]
                    ndist = math.hypot(ndx, ndy)

                    if ndist > 0:
                        # Đi tiếp phần đường còn dư ngay trong Frame này
                        self.pixel_pos[0] += (ndx / ndist) * remainder
                        self.pixel_pos[1] += (ndy / ndist) * remainder

                        if ndx > 0: self.direction = "right"
                        elif ndx < 0: self.direction = "left"
                        elif ndy > 0: self.direction = "down"
                        elif ndy < 0: self.direction = "up"
            else:
                self.pixel_pos[0] += (dx / distance) * actual_speed
                self.pixel_pos[1] += (dy / distance) * actual_speed

        self._animate(anim_state, speed_multiplier)

    def _animate(self, state, speed_multiplier):
        current_anim_list = self.animations[state][self.direction]
        self.current_frame += self.animation_speed * speed_multiplier
        if self.current_frame >= len(current_anim_list): self.current_frame = 0
        self.image = current_anim_list[int(self.current_frame)]

    def draw(self, surface, offset_x=0, offset_y=0):
        center_x = int(self.pixel_pos[0]) + offset_x + (self.tile_size // 2)
        center_y = int(self.pixel_pos[1]) + offset_y + (self.tile_size // 2)
        rect = self.image.get_rect(center=(center_x, center_y))
        rect.y -= 8
        surface.blit(self.image, rect)
        self.debuffs.draw_effects(surface, offset_x, offset_y)