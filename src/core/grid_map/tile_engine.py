"""
📄 File: src/core/grid_map/tile_engine.py
* Trạng thái: Ổn định (Stable).
* Tính năng: Tiền xử lý scale toàn ảnh, tự đo kích thước, báo lỗi khối tím.
"""
import pygame
import os

# Trở về bộ từ điển nguyên gốc cực kỳ ổn định
WALL_BASE_GIDS = {
    0: 105, 1: 263, 2: 222, 4: 159, 8: 226, 5: 185, 10: 225, 6: 183, 12: 184,
    3: 227, 9: 228, 15: 224, 7: 224, 11: 224, 13: 224, 14: 224
}
WALL_ROOF_GIDS = {
    2: 196, 8: 200, 10: 197, 6: 162, 12: 163, 3: 201, 9: 202,
    15: 198, 7: 161, 11: 187, 13: 186, 14: 173
}

class TileEngine:
    def __init__(self, image_path: str, scale: int = 2):
        self.scale = scale
        self.original_size = 16
        self.tile_size = self.original_size * self.scale
        self.image_cache = {}

        self.master_image = self._load_and_scale_master_image(image_path)

        if self.master_image:
            self.columns = self.master_image.get_width() // self.tile_size
            self.rows = self.master_image.get_height() // self.tile_size
            self.max_tiles = self.columns * self.rows
        else:
            self.columns = 1
            self.max_tiles = 0

        self.fallback_tile = pygame.Surface((self.tile_size, self.tile_size))
        self.fallback_tile.fill((255, 0, 255))

    def _load_and_scale_master_image(self, path: str):
        if not os.path.exists(path):
            return None
        raw_image = pygame.image.load(path).convert_alpha()
        w, h = raw_image.get_size()
        return pygame.transform.scale(raw_image, (w * self.scale, h * self.scale))

    def get_tile(self, gid: int) -> pygame.Surface:
        if gid == 0:
            return None
        if gid < 0 or gid > self.max_tiles or self.master_image is None:
            return self.fallback_tile

        if gid in self.image_cache:
            return self.image_cache[gid]

        local_id = gid - 1
        col, row = local_id % self.columns, local_id // self.columns
        x, y = col * self.tile_size, row * self.tile_size

        try:
            rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
            tile_surface = self.master_image.subsurface(rect)
            self.image_cache[gid] = tile_surface
            return tile_surface
        except ValueError:
            return self.fallback_tile