"""
📄 Tên File: grid_map.py (Nằm trong src/core/)
* Vai trò: Load bản đồ .tmx, render đồ họa bằng pytmx và trích xuất ma trận va chạm cho AI.
"""

import pytmx
import pygame

class GridMap:
    def __init__(self, tmx_filepath: str, scale: int = 2):
        self.scale = scale
        try:
            # Load TMX. Yêu cầu file ảnh (walls_floor.png) phải nằm cùng thư mục với file tmx.
            self.tmx_data = pytmx.load_pygame(tmx_filepath, pixelalpha=True)
            self.width = self.tmx_data.width
            self.height = self.tmx_data.height
            self.tile_size = self.tmx_data.tilewidth * self.scale

            # Khởi tạo ma trận rỗng toàn số 0 (Có thể đi được)
            self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
            self._build_collision_grid()
            print(f"✅ Đã tải map TMX {self.width}x{self.height} thành công!")
        except Exception as e:
            print(f"⚠️ Lỗi tải map TMX: {e}")
            self.tmx_data = None
            self.width, self.height, self.tile_size = 10, 10, 32
            self.grid = [[0]*10 for _ in range(10)]

    def _build_collision_grid(self):
        """Quét layer 'Structure' (ID=1) để xác định Tường."""
        try:
            struct_layer = self.tmx_data.get_layer_by_name("Structure")
            for x, y, gid in struct_layer:
                if gid != 0: # Nếu có khối block thì đánh dấu là 1 (Tường)
                    self.grid[y][x] = 1
        except ValueError:
            print("⚠️ Cảnh báo: Không tìm thấy layer tên 'Structure' trong file TMX.")

    def render(self, surface: pygame.Surface, camera_offset: pygame.Vector2):
        """Vẽ toàn bộ map lên một bề mặt, có tính đến góc nhìn Camera."""
        if not self.tmx_data: return

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        scaled_tile = pygame.transform.scale(tile, (self.tile_size, self.tile_size))
                        draw_x = x * self.tile_size - camera_offset.x
                        draw_y = y * self.tile_size - camera_offset.y
                        surface.blit(scaled_tile, (draw_x, draw_y))

    def is_walkable(self, grid_x: int, grid_y: int) -> bool:
        if grid_x < 0 or grid_x >= self.width or grid_y < 0 or grid_y >= self.height:
            return False
        return self.grid[grid_y][grid_x] == 0