"""
📄 File: src/core/grid_map/map_controller.py
* Vai trò: Bộ não quản lý logic ma trận đa tầng.
* Cập nhật: Thêm nhận diện Bẫy Tử Thần (Trap - ID: 99).
"""
from collections import deque

class MapController:
    def __init__(self, raw_layers_data: dict, layer_names: list, raw_objects: list,
                 original_width: int, original_height: int, tile_size: int = 16,
                 base_layer_name: str = "Floor", solid_layer_name: str = "Structure"):

        self.width = original_width + 2
        self.height = original_height + 2
        self.layer_names = layer_names

        self.base_layer_name = base_layer_name
        self.solid_layer_name = solid_layer_name

        self.expanded_layers = {}

        # Mảng collision_grid giờ chứa: 0 (Sàn), 1 (Tường), 3 (Băng), 4 (Sương mù), 5 (Bùn), 99 (Bẫy chết)
        self.collision_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.boss_walls = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.border_walls = [[0 for _ in range(self.width)] for _ in range(self.height)]

        self.start_points = []
        self.goal_point = None

        self._build_expanded_grids(raw_layers_data, original_width, original_height)
        self._translate_objects(raw_objects, tile_size)

    def _build_expanded_grids(self, raw_layers_data: dict, ow: int, oh: int):
        for name in self.layer_names:
            self.expanded_layers[name] = [[0 for _ in range(self.width)] for _ in range(self.height)]

            if name == self.base_layer_name:
                for y in range(self.height):
                    for x in range(self.width):
                        self.expanded_layers[name][y][x] = 80

            for y in range(oh):
                for x in range(ow):
                    gid = raw_layers_data[name][y][x]
                    self.expanded_layers[name][y + 1][x + 1] = gid

                    # Gán Tường (1)
                    if name == self.solid_layer_name and gid != 0:
                        self.collision_grid[y + 1][x + 1] = 1

                    # Gán Bùn Lầy (5)
                    elif name == "Mud_floor" and gid != 0:
                        if self.collision_grid[y + 1][x + 1] != 1:
                            self.collision_grid[y + 1][x + 1] = 5

                    # Gán Băng Trơn (3)
                    elif name == "Ice_floor" and gid != 0:
                        if self.collision_grid[y + 1][x + 1] != 1:
                            self.collision_grid[y + 1][x + 1] = 3

                    # Gán Sương Mù (4) - Hỗ trợ cả Fog và Frog
                    elif name in ["Fog", "Frog"] and gid != 0:
                        if self.collision_grid[y + 1][x + 1] != 1:
                            self.collision_grid[y + 1][x + 1] = 4

                    # [MỚI]: Gán Bẫy Tử Thần (99)
                    elif name.lower() == "trap" and gid != 0:
                        if self.collision_grid[y + 1][x + 1] != 1:
                            self.collision_grid[y + 1][x + 1] = 99

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
        return self.collision_grid[y][x] != 1

    def _check_path_exists(self, start_pos: tuple, goal_pos: tuple) -> bool:
        if not self.is_walkable(*start_pos) or not self.is_walkable(*goal_pos):
            return False

        queue = deque([start_pos])
        visited = set([start_pos])

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == goal_pos:
                return True

            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.collision_grid[ny][nx] != 1 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        return False

    def place_boss_wall(self, x: int, y: int, hero_pos: tuple, goal_pos: tuple) -> str:
        if not self.is_walkable(x, y):
            return "INVALID"

        old_value = self.collision_grid[y][x]

        self.collision_grid[y][x] = 1
        self.boss_walls[y][x] = 1

        if self._check_path_exists(hero_pos, goal_pos):
            return "SUCCESS"
        else:
            self.collision_grid[y][x] = old_value
            self.boss_walls[y][x] = 0
            return "BLOCKED"

    def remove_boss_wall(self, x: int, y: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.boss_walls[y][x] == 1:
                self.boss_walls[y][x] = 0
                self.collision_grid[y][x] = 0

                # Khôi phục các lớp sàn nếu đập bỏ tường
                if self.expanded_layers.get("Mud_floor") and self.expanded_layers["Mud_floor"][y][x] != 0:
                    self.collision_grid[y][x] = 5
                elif self.expanded_layers.get("Ice_floor") and self.expanded_layers["Ice_floor"][y][x] != 0:
                    self.collision_grid[y][x] = 3
                elif (self.expanded_layers.get("Fog") and self.expanded_layers["Fog"][y][x] != 0) or \
                        (self.expanded_layers.get("Frog") and self.expanded_layers["Frog"][y][x] != 0):
                    self.collision_grid[y][x] = 4
                # [MỚI]: Khôi phục Bẫy Tử Thần
                elif (self.expanded_layers.get("Trap") and self.expanded_layers["Trap"][y][x] != 0) or \
                        (self.expanded_layers.get("trap") and self.expanded_layers["trap"][y][x] != 0):
                    self.collision_grid[y][x] = 99
                return True
        return False

    def get_boss_bitmask(self, x: int, y: int) -> int:
        mask = 0
        def is_wall(nx, ny):
            if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height: return True
            return self.collision_grid[ny][nx] == 1

        if is_wall(x, y - 1): mask += 1
        if is_wall(x + 1, y): mask += 2
        if is_wall(x, y + 1): mask += 4
        if is_wall(x - 1, y): mask += 8

        return mask