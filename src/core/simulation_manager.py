"""
📄 Tên File: simulation_manager.py (Nằm trong src/core/)
"""
import pygame

class SimulationManager:
    def __init__(self, tile_size):
        self.tile_size = tile_size
        self.algo_gen = None

        self.visited = set()
        self.frontier = []
        self.path = []
        self.history = [] # Dùng cho rewind

        # Khởi tạo các cọ vẽ mờ
        self.surf_visited = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_visited.fill((173, 216, 230, 150))
        self.surf_frontier = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_frontier.fill((241, 196, 15, 150))
        self.surf_path = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_path.fill((155, 89, 182, 180))

    def start(self, algo_func, grid, start_node, goal_node):
        """Khởi tạo thuật toán và xóa cache."""
        self.algo_gen = algo_func(grid, start_node, goal_node)
        self.visited.clear()
        self.frontier.clear()
        self.path.clear()
        self.history.clear()

    def step(self):
        """Tiến lên 1 frame mô phỏng. Trả về True nếu tìm thấy đường đi."""
        try:
            _, frontier_rc, visited_rc, path_rc = next(self.algo_gen)
            self.history = [(c, r) for r, c in visited_rc]
            self.visited = set(self.history)
            self.frontier = [(c, r) for r, c in frontier_rc]
            self.path = [(c, r) for r, c in path_rc]

            return bool(self.path) # Trả về True nếu đường đi (path) đã được tìm thấy
        except StopIteration:
            return False

    def rewind_step(self):
        """Lùi lại 1 frame (Xóa 3 node 1 lúc cho nhanh). Trả về node lùi của Hero."""
        for _ in range(3):
            if self.history:
                self.history.pop()
        self.visited = set(self.history)
        self.frontier.clear()

        # Rút đường đi để Hero đi lùi
        if self.path:
            return self.path.pop()
        return None

    def is_rewind_finished(self):
        return not self.history and not self.path

    def draw(self, surface):
        """Vẽ toàn bộ trạng thái lên map."""
        for x, y in self.visited:
            surface.blit(self.surf_visited, (x * self.tile_size, y * self.tile_size))
        for x, y in self.frontier:
            surface.blit(self.surf_frontier, (x * self.tile_size, y * self.tile_size))
        for x, y in self.path:
            surface.blit(self.surf_path, (x * self.tile_size, y * self.tile_size))