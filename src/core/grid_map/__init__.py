"""
📄 File: src/core/grid_map/__init__.py
* Trạng thái: Ổn định (Stable). Tường TMX giữ nguyên bản, Tường Boss dùng Bitmask.
* Tính năng: Vẫn giữ Sandwich Rendering (3 lớp) để Hero đi sau mái nhà.
"""
import pygame
import os
from .map_loader import MapLoader
from .tile_engine import TileEngine, WALL_BASE_GIDS, WALL_ROOF_GIDS
from .map_controller import MapController

class GridMap:
    def __init__(self, tmx_filepath: str, scale: int = 2):
        self.scale = scale
        self.loader = MapLoader(tmx_filepath)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        image_path = os.path.join(project_root, "assets", "images", "walls_floor.png")

        self.tile_engine = TileEngine(image_path, self.scale)
        self.tile_size = self.tile_engine.tile_size

        self.controller = MapController(
            raw_layers_data=self.loader.layers_data,
            layer_names=self.loader.layer_names,
            raw_objects=self.loader.objects,
            original_width=self.loader.raw_width,
            original_height=self.loader.raw_height,
            tile_size=self.loader.tile_size,
            base_layer_name="Floor",
            solid_layer_name="Structure"
        )

        self.width = self.controller.width
        self.height = self.controller.height
        self.grid = self.controller.collision_grid
        self.boss_walls = self.controller.boss_walls
        self.start_points = self.controller.start_points
        self.goal_point = self.controller.goal_point

    def is_walkable(self, grid_x: int, grid_y: int) -> bool:
        return self.controller.is_walkable(grid_x, grid_y)

    def place_boss_wall(self, grid_x: int, grid_y: int, hero_pos: tuple, goal_pos: tuple) -> str:
        return self.controller.place_boss_wall(grid_x, grid_y, hero_pos, goal_pos)

    def remove_boss_wall(self, grid_x: int, grid_y: int) -> bool:
        return self.controller.remove_boss_wall(grid_x, grid_y)

    def get_boss_bitmask(self, grid_x: int, grid_y: int) -> int:
        return self.controller.get_boss_bitmask(grid_x, grid_y)

    def render(self, surface: pygame.Surface, camera_offset=None):
        self.render_bottom(surface, camera_offset)
        self.render_top(surface, camera_offset)

    def render_bottom(self, surface: pygame.Surface, camera_offset=None):
        """LỚP 1: Sàn nhà, Cấu trúc tĩnh TMX, và CHÂN TƯỜNG Boss."""
        if camera_offset is None: camera_offset = pygame.Vector2(0, 0)

        for layer_name in self.controller.layer_names:
            if layer_name == "Foreground": continue

            layer_grid = self.controller.expanded_layers.get(layer_name)
            if not layer_grid: continue

            for y in range(self.height):
                for x in range(self.width):
                    pixel_x = x * self.tile_size - camera_offset.x
                    pixel_y = y * self.tile_size - camera_offset.y

                    gid = layer_grid[y][x]
                    if gid != 0:
                        tile_surface = self.tile_engine.get_tile(gid)
                        if tile_surface:
                            # [MỚI]: Nhuộm màu dựa theo Tên Layer
                            if layer_name == "Mud_floor":
                                tint = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                                tint.fill((101, 67, 33, 160)) # Nhuộm Bùn Nâu Mờ
                                final_surface = tile_surface.copy()
                                final_surface.blit(tint, (0, 0))
                                surface.blit(final_surface, (pixel_x, pixel_y))
                            elif layer_name == "Ice_floor":
                                tint = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                                tint.fill((150, 220, 255, 120)) # Nhuộm Xanh Băng Trơn
                                final_surface = tile_surface.copy()
                                final_surface.blit(tint, (0, 0))
                                surface.blit(final_surface, (pixel_x, pixel_y))
                            else:
                                surface.blit(tile_surface, (pixel_x, pixel_y))

        for y in range(self.height):
            for x in range(self.width):
                is_boss = self.controller.boss_walls[y][x] == 1
                is_border = self.controller.border_walls[y][x] == 1

                if is_boss or is_border:
                    mask = self.controller.get_boss_bitmask(x, y)
                    pixel_x = x * self.tile_size - camera_offset.x
                    pixel_y = y * self.tile_size - camera_offset.y

                    base_gid = WALL_BASE_GIDS.get(mask, 185)
                    base_surface = self.tile_engine.get_tile(base_gid)
                    if base_surface:
                        surface.blit(base_surface, (pixel_x, pixel_y))

    def render_top(self, surface: pygame.Surface, camera_offset=None):
        """LỚP 3: Vẽ NÓC TƯỜNG Boss và FOREGROUND TMX."""
        if camera_offset is None: camera_offset = pygame.Vector2(0, 0)

        # 1. Vẽ Mái (Roof) của tường Boss
        for y in range(self.height):
            for x in range(self.width):
                is_boss = self.controller.boss_walls[y][x] == 1
                is_border = self.controller.border_walls[y][x] == 1

                if is_boss or is_border:
                    mask = self.controller.get_boss_bitmask(x, y)
                    pixel_x = x * self.tile_size - camera_offset.x
                    pixel_y = y * self.tile_size - camera_offset.y

                    roof_gid = WALL_ROOF_GIDS.get(mask, 0)
                    if roof_gid > 0 and y > 0:
                        roof_surface = self.tile_engine.get_tile(roof_gid)
                        if roof_surface:
                            surface.blit(roof_surface, (pixel_x, pixel_y - self.tile_size))

        # 2. Vẽ Foreground TMX
        if "Foreground" in self.controller.layer_names:
            layer_grid = self.controller.expanded_layers.get("Foreground")
            if layer_grid:
                for y in range(self.height):
                    for x in range(self.width):
                        pixel_x = x * self.tile_size - camera_offset.x
                        pixel_y = y * self.tile_size - camera_offset.y

                        gid = layer_grid[y][x]
                        if gid != 0:
                            tile_surface = self.tile_engine.get_tile(gid)
                            if tile_surface:
                                surface.blit(tile_surface, (pixel_x, pixel_y))