"""
📄 Tên File: simulation_manager.py (Nằm trong src/core/)
* Cập nhật: Sửa lỗi nghiêm trọng cộng dồn CPU. Code mới sử dụng bộ đếm delta an toàn tuyệt đối.
* Cập nhật mới nhất: Thêm cơ chế Pause thuật toán khi Hero đang trong trạng thái is_dead hoặc is_resurrecting.
"""
import pygame

class SimulationManager:
    def __init__(self, tile_size):
        self.tile_size = tile_size
        self.algo_gen = None
        self.grid = None

        self.current = None
        self.visited = set()
        self.frontier = []
        self.path = []
        self.history = []
        self.metrics = {}

        self.cpu_usage = 0

        self.surf_visited = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_visited.fill((173, 216, 230, 150))
        self.surf_frontier = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_frontier.fill((241, 196, 15, 150))
        self.surf_path = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        self.surf_path.fill((155, 89, 182, 180))

    def start(self, algo_func, grid, start_node, goal_node):
        self.grid = grid
        self.algo_gen = algo_func(grid, start_node, goal_node)
        self.current = None
        self.visited.clear()
        self.frontier.clear()
        self.path.clear()
        self.history.clear()
        self.metrics.clear()
        self.cpu_usage = 0

    def _recalc_cpu(self):
        """Hàm tiện ích: Tính lại toàn bộ CPU từ tập visited hiện tại. Tránh lỗi Desync khi tua ngược."""
        self.cpu_usage = 0
        for x, y in self.visited:
            if self.grid and 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                if self.grid[y][x] == 4: # Sương mù (Layer Fog/Frog)
                    self.cpu_usage += 5
                else:
                    self.cpu_usage += 1

    def step(self):
        try:
            yielded_data = next(self.algo_gen)

            if len(yielded_data) == 4:
                current_rc, visited_rc, frontier_rc, path_rc = yielded_data
                self.metrics = {}
            else:
                current_rc, visited_rc, frontier_rc, path_rc, metrics_data = yielded_data
                self.metrics = metrics_data

            self.current = current_rc

            # 1. Đồng nhất tọa độ (X, Y)
            self.history = [(c, r) for r, c in visited_rc]
            new_visited_xy = set(self.history)

            # 2. Phép trừ an toàn: Lọc ra chính xác những ô MỚI được quét trong Frame này
            added_nodes = new_visited_xy - self.visited

            # 3. Cộng điểm CPU
            for x, y in added_nodes:
                if self.grid and 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                    if self.grid[y][x] == 4:
                        self.cpu_usage += 5 # Quét vào sương mù tốn 5 Trí lực
                    else:
                        self.cpu_usage += 1 # Bình thường tốn 1 Trí lực

            # 4. Lưu trạng thái
            self.visited = new_visited_xy
            self.frontier = [(c, r) for r, c in frontier_rc]

            if path_rc is not None:
                self.path = [(c, r) for r, c in path_rc]
            else:
                self.path = []

            return bool(self.path)
        except StopIteration:
            self.current = None
            return False

    def rewind_step(self):
        for _ in range(3):
            if self.history:
                self.history.pop()

        self.visited = set(self.history)
        self.frontier.clear()

        # [QUAN TRỌNG]: Bắt buộc phải tính lại CPU khi tua ngược để đồng bộ với số ô UI
        self._recalc_cpu()

        if self.path:
            return self.path.pop()
        return None

    def is_rewind_finished(self):
        return not self.history and not self.path

    def draw(self, surface):
        for x, y in self.visited:
            surface.blit(self.surf_visited, (x * self.tile_size, y * self.tile_size))
        for x, y in self.frontier:
            surface.blit(self.surf_frontier, (x * self.tile_size, y * self.tile_size))
        for x, y in self.path:
            surface.blit(self.surf_path, (x * self.tile_size, y * self.tile_size))

    def process_execution(self, scene):
        # [TÁCH BIỆT LOGIC]: Tuyệt đối không chạy thuật toán nếu Hero đang nằm chết/hồi sinh
        if getattr(scene.hero, 'is_resurrecting', False) or getattr(scene.hero, 'is_dead', False):
            scene.sim_speed_counter = 0 # Xóa bộ đếm để không bị tua nhanh sau khi tỉnh dậy
            return

        scene.sim_speed_counter += scene.dashboard.current_speed
        while scene.sim_speed_counter >= 1.0:
            scene.sim_speed_counter -= 1.0
            path_found = self.step()

            local_search_algos = ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM", "LRTA_STAR"]

            if scene.dashboard.selected_algo in local_search_algos:
                current_node = self.current

                has_valid_node = False
                if current_node is not None:
                    if isinstance(current_node, list):
                        if len(current_node) > 0: has_valid_node = True
                    else:
                        has_valid_node = True

                if has_valid_node:
                    target_y, target_x = current_node[0] if isinstance(current_node, list) else current_node
                    if (target_x, target_y) != tuple(scene.hero.grid_pos):
                        scene.hero.set_path([tuple(scene.hero.grid_pos), (target_x, target_y)])
                        scene.phase_manager.set_state("MOVING")
                        scene.sim_speed_counter = 0
                        break

                if not has_valid_node or not self.frontier:
                    if tuple(scene.hero.grid_pos) == scene.goal_pos:
                        if scene.phase_manager.current_phase == "HERO":
                            scene.phase_manager.trigger_success()
                        else:
                            scene.phase_manager.trigger_failure("DEFENSE BROKEN: GHOST REACHED THE GOAL")
                    else:
                        if scene.phase_manager.current_phase == "HERO":
                            scene.phase_manager.trigger_failure("MẮC KẸT VÀ HẾT LƯỢT DỊCH CHUYỂN!")
                        else:
                            print("💀 BOSS CHẶN ĐƯỜNG THÀNH CÔNG!")
                            scene.phase_manager.trigger_success()
                    scene.sim_speed_counter = 0
                    break

            else:
                if path_found:
                    scene.hero.set_path(self.path)
                    scene.phase_manager.set_state("MOVING")
                    scene.sim_speed_counter = 0
                    break
                elif not self.frontier:
                    if scene.phase_manager.current_phase == "HERO":
                        scene.phase_manager.trigger_failure("PATH NOT FOUND: VÉT CẠN BẢN ĐỒ")
                    else:
                        scene.phase_manager.trigger_success()
                    scene.sim_speed_counter = 0
                    break