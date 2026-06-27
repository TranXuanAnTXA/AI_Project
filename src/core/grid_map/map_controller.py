"""
📄 File: src/core/grid_map/map_controller.py
* Vai trò: Bộ não quản lý logic ma trận đa tầng.
* Tính năng: Mở rộng 32x32, Dịch chuyển tọa độ Object, Bitmask siêu tốc và BFS chống chặn đường.
* Cập nhật: Layer linh hoạt (Agnostic Layering) triệt tiêu hoàn toàn Hardcode.
"""
from collections import deque

class MapController:
    # Bổ sung 2 tham số base_layer_name và solid_layer_name để làm layer linh hoạt
    def __init__(self, raw_layers_data: dict, layer_names: list, raw_objects: list,
                 original_width: int, original_height: int, tile_size: int = 16,
                 base_layer_name: str = "Floor", solid_layer_name: str = "Structure"):

        self.width = original_width + 2
        self.height = original_height + 2
        self.layer_names = layer_names

        self.base_layer_name = base_layer_name
        self.solid_layer_name = solid_layer_name

        self.expanded_layers = {}

        # Hợp nhất: Tất cả viền, tường TMX cũ, và tường Boss đều lưu chung vào collision_grid
        self.collision_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.boss_walls = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.border_walls = [[0 for _ in range(self.width)] for _ in range(self.height)]

        self.start_points = []
        self.goal_point = None

        # 1. Trải lưới và xây viền
        self._build_expanded_grids(raw_layers_data, original_width, original_height)

        # 2. Dịch chuyển tọa độ Hero / Goal cho khớp với ma trận 32x32
        self._translate_objects(raw_objects, tile_size)

    def _build_expanded_grids(self, raw_layers_data: dict, ow: int, oh: int):
        # Khởi tạo mảng 32x32 cho TẤT CẢ layer
        for name in self.layer_names:
            self.expanded_layers[name] = [[0 for _ in range(self.width)] for _ in range(self.height)]

            # XỬ LÝ LAYER LINH HOẠT: Không dùng "Floor" hay "Structure" cứng nữa
            # Trải gạch nền (GID 80) lấp đầy khoảng trống cho Base Layer
            if name == self.base_layer_name:
                for y in range(self.height):
                    for x in range(self.width):
                        self.expanded_layers[name][y][x] = 80

            # Nhúng dữ liệu 30x30 vào giữa ma trận 32x32 (tịnh tiến x+1, y+1)
            for y in range(oh):
                for x in range(ow):
                    gid = raw_layers_data[name][y][x]
                    self.expanded_layers[name][y + 1][x + 1] = gid

                    # Cập nhật lưới va chạm nếu đây là Solid Layer
                    if name == self.solid_layer_name and gid != 0:
                        self.collision_grid[y + 1][x + 1] = 1

        # Đổ bê tông làm Viền Vĩnh Cửu
        for x in range(self.width):
            self._set_border(x, 0)
            self._set_border(x, self.height - 1)
        for y in range(self.height):
            self._set_border(0, y)
            self._set_border(self.width - 1, y)

    def _set_border(self, x: int, y: int):
        self.border_walls[y][x] = 1
        self.collision_grid[y][x] = 1

    def _translate_objects(self, raw_objects: list, tile_size: int):
        """Chuyển đổi Pixel -> Grid và cộng thêm offset mở rộng viền (+1)"""
        for obj in raw_objects:
            grid_x = int(obj['x'] // tile_size) + 1
            grid_y = int(obj['y'] // tile_size) + 1

            name = obj['name'].strip().lower()
            if name == 'start':
                self.start_points.append((grid_x, grid_y))
            elif name == 'goal':
                self.goal_point = (grid_x, grid_y)

    def is_walkable(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.width or y < 0 or y >= self.height: return False
        return self.collision_grid[y][x] == 0

    def _check_path_exists(self, start_pos: tuple, goal_pos: tuple) -> bool:
        """Thuật toán BFS 'Bóng đêm': Chạy cực nhanh không lưu vết."""
        if not self.is_walkable(*start_pos) or not self.is_walkable(*goal_pos):
            return False

        queue = deque([start_pos])
        visited = set([start_pos])

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == goal_pos:
                return True # Đã tìm thấy đường

            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.collision_grid[ny][nx] == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        return False

    def place_boss_wall(self, x: int, y: int, hero_pos: tuple, goal_pos: tuple) -> str:
        """Trả về: "SUCCESS" (đặt được), "BLOCKED" (chặn đường -> vỡ), "INVALID" (đè vật cản)."""
        if not self.is_walkable(x, y):
            return "INVALID"

        # 1. Đặt thử tường (Try)
        self.collision_grid[y][x] = 1
        self.boss_walls[y][x] = 1

        # 2. Kiểm tra BFS
        if self._check_path_exists(hero_pos, goal_pos):
            return "SUCCESS"
        else:
            # 3. Kẹt đường -> Rollback
            self.collision_grid[y][x] = 0
            self.boss_walls[y][x] = 0
            return "BLOCKED"

    def remove_boss_wall(self, x: int, y: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.boss_walls[y][x] == 1:
                self.collision_grid[y][x] = 0
                self.boss_walls[y][x] = 0
                return True
        return False

    def get_boss_bitmask(self, x: int, y: int) -> int:
        """Bitmask siêu tốc quét trên collision_grid"""
        mask = 0
        def is_wall(nx, ny):
            if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height: return True
            return self.collision_grid[ny][nx] == 1

        if is_wall(x, y - 1): mask += 1 # Bắc
        if is_wall(x + 1, y): mask += 2 # Đông
        if is_wall(x, y + 1): mask += 4 # Nam
        if is_wall(x - 1, y): mask += 8 # Tây

        return mask


if __name__ == "__main__":
    # ---------------------------------------------------------
    # HÀM MAIN TEST: KIỂM CHỨNG BFS VÀ TRANSLATOR
    # ---------------------------------------------------------
    import os
    from map_loader import MapLoader

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    test_tmx_path = os.path.join(project_root, "assets", "maps", "dungeon_map_1.tmx")

    if os.path.exists(test_tmx_path):
        loader = MapLoader(test_tmx_path)
        controller = MapController(loader.layers_data, loader.layer_names, loader.objects,
                                   loader.raw_width, loader.raw_height, loader.tile_size)

        print("\n1. KIỂM TRA DỊCH CHUYỂN TỌA ĐỘ OBJECT (Shift +1)")
        print(f"- Start Points mới : {controller.start_points}")
        print(f"- Goal Point mới   : {controller.goal_point}")

        print("\n2. KIỂM TRA THUẬT TOÁN CHỐNG CHẶN ĐƯỜNG (BFS BÓNG ĐÊM)")
        # Giả lập Hero đang đứng ở ô trống (2, 2) và Goal ở (5, 5)
        hero_pos = (2, 2)
        goal_pos = (5, 5)

        print(f"Hero đang đứng tại {hero_pos}, Goal tại {goal_pos}")

        # Xây 3 bức tường vây quanh Hero (Bắc, Đông, Nam)
        print(f"- Đặt tường Bắc {2,1}:", controller.place_boss_wall(2, 1, hero_pos, goal_pos))
        print(f"- Đặt tường Đông {3,2}:", controller.place_boss_wall(3, 2, hero_pos, goal_pos))
        print(f"- Đặt tường Nam {2,3}:", controller.place_boss_wall(2, 3, hero_pos, goal_pos))

        # Lúc này Hero chỉ còn cửa thoát duy nhất ở hướng Tây (1, 2)
        print("-> Cố tình xây nốt bức tường Tây (1, 2) để nhốt Hero...")
        result = controller.place_boss_wall(1, 2, hero_pos, goal_pos)

        if result == "BLOCKED":
            print(f"✅ Hệ thống đáp trả: '{result}' -> Thuật toán BFS đã hoạt động hoàn hảo, bảo vệ Hero khỏi bị nhốt!")
        else:
            print(f"❌ Lỗi: Hệ thống trả về {result}. Hero đã bị nhốt thành công (Lỗi game).")

    else:
        print(f"❌ Không tìm thấy file TMX để test!")