import math
import random
import copy
from collections import deque
from src.algorithms.common import Coordinate

def get_updated_grid(grid, known_traps):
    """
    Tạo grid mới. Biến toàn bộ bẫy TRONG TRÍ NHỚ thành tường cứng (1).
    """
    new_grid = copy.deepcopy(grid)

    for trap in known_traps:
        tx, ty = trap.get("grid_x", -1), trap.get("grid_y", -1)
        tw, th = trap.get("grid_width", 1), trap.get("grid_height", 1)

        for x in range(tx, tx + tw):
            for y in range(ty, ty + th):
                if 0 <= y < len(new_grid) and 0 <= x < len(new_grid[0]):
                    new_grid[y][x] = 1

    return new_grid

def compute_distance_map(grid, goal_pos):
    rows, cols = len(grid), len(grid[0])
    dist_map = [[math.inf for _ in range(cols)] for _ in range(rows)]

    queue = deque([(goal_pos, 0)])
    dist_map[goal_pos[1]][goal_pos[0]] = 0

    while queue:
        (cx, cy), d = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < rows and 0 <= nx < cols:
                if grid[ny][nx] != 1 and dist_map[ny][nx] == math.inf:
                    dist_map[ny][nx] = d + 1
                    queue.append(((nx, ny), d + 1))

    return dist_map

class GameState:
    def __init__(self, grid, dist_map, hero_pos: Coordinate, boss_pos: Coordinate, goal_pos: Coordinate, hero_history: list, traps_list: list):
        self.grid = grid
        self.dist_map = dist_map
        self.hero_pos = hero_pos
        self.boss_pos = boss_pos
        self.goal_pos = goal_pos
        self.hero_history = hero_history
        self.traps_list = traps_list
        self.rows = len(grid)
        self.cols = len(grid[0])

    def get_legal_actions(self, agent_index: int, is_expectimax: bool = False):
        legal_actions = []
        pos = self.hero_pos if agent_index == 0 else self.boss_pos
        moves = [((0, -1), "UP"), ((0, 1), "DOWN"), ((-1, 0), "LEFT"), ((1, 0), "RIGHT")]

        for (dx, dy), action in moves:
            nx, ny = pos[0] + dx, pos[1] + dy
            # Kiểm tra không ra ngoài map và không tông tường
            if 0 <= ny < self.rows and 0 <= nx < self.cols and self.grid[ny][nx] != 1:

                # Nếu là Hero (0) và KHÔNG PHẢI Expectimax, ép coi bẫy là Tường!
                if agent_index == 0 and not is_expectimax:
                    if self.is_on_trap((nx, ny)):
                        continue # Bỏ qua hoàn toàn hướng đi này

                legal_actions.append(action)

        return legal_actions if legal_actions else ["STOP"]

    def generate_successor(self, agent_index: int, action: str):
        move_dict = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0), "STOP": (0, 0)}
        dx, dy = move_dict.get(action, (0, 0))

        new_hero = self.hero_pos
        new_boss = self.boss_pos

        if agent_index == 0:
            new_hero = (self.hero_pos[0] + dx, self.hero_pos[1] + dy)
        else:
            new_boss = (self.boss_pos[0] + dx, self.boss_pos[1] + dy)

        return GameState(self.grid, self.dist_map, new_hero, new_boss, self.goal_pos, self.hero_history, self.traps_list)

    def is_terminal(self):
        if self.hero_pos == self.boss_pos: return True
        if self.hero_pos == self.goal_pos: return True
        return False

    def is_on_trap(self, pos) -> bool:
        for trap in self.traps_list:
            tx, ty = trap.get("grid_x", -1), trap.get("grid_y", -1)
            tw, th = trap.get("grid_width", 1), trap.get("grid_height", 1)
            if tx <= pos[0] < tx + tw and ty <= pos[1] < ty + th:
                return True
        return False

    def min_dist_to_trap(self) -> int:
        if not self.traps_list:
            return math.inf

        min_d = math.inf
        for trap in self.traps_list:
            tx, ty = trap.get("grid_x", -1), trap.get("grid_y", -1)
            tw, th = trap.get("grid_width", 1), trap.get("grid_height", 1)
            dx = max(tx - self.hero_pos[0], 0, self.hero_pos[0] - (tx + tw - 1))
            dy = max(ty - self.hero_pos[1], 0, self.hero_pos[1] - (ty + th - 1))
            min_d = min(min_d, dx + dy)

        return min_d

    def evaluate(self, is_expectimax=False) -> float:
        if self.hero_pos == self.boss_pos: return -999999
        if self.hero_pos == self.goal_pos: return 999999

        dist_to_goal = self.dist_map[self.hero_pos[1]][self.hero_pos[0]]
        dist_to_boss = abs(self.hero_pos[0] - self.boss_pos[0]) + abs(self.hero_pos[1] - self.boss_pos[1])

        score = 0

        # [GIẢI QUYẾT LỖI TUYỆT VỌNG]
        # Phạt kẹt đường (-50000) nhỏ hơn rủi ro bẫy 10% (-100000).
        # Khiến Hero thà chạy luẩn quẩn khi Boss ở xa, chứ không đạp bẫy.
        if dist_to_goal == math.inf:
            score -= 50000
        else:
            score -= dist_to_goal * 20

        # Áp lực từ Boss (Dù kẹt đường vẫn phải cố lùi xa Boss nhất có thể)
        if dist_to_boss <= 4:
            score -= (5 - dist_to_boss) * 1000
        else:
            score += dist_to_boss * 2

        if self.hero_pos in self.hero_history:
            score -= 15

        trap_dist = self.min_dist_to_trap()
        if is_expectimax and trap_dist == 0:
            score -= 200

        return score


# ==========================================
# CÁC THUẬT TOÁN TÌM KIẾM
# ==========================================

def get_best_action_minimax(grid, hero_pos, boss_pos, goal_pos, hero_history, known_traps, max_depth=3) -> str:
    # 1. Cập nhật bản đồ: phát hiện bẫy TRONG TRÍ NHỚ và biến nó thành tường
    updated_grid = get_updated_grid(grid, known_traps)
    # 2. Truyền bản đồ MỚI vào BFS để tìm đường đi né bẫy
    dist_map = compute_distance_map(updated_grid, goal_pos)
    # 3. Khởi tạo GameState với bản đồ MỚI
    initial_state = GameState(updated_grid, dist_map, hero_pos, boss_pos, goal_pos, hero_history, known_traps)

    def min_value(state: GameState, depth: int):
        if depth == 0 or state.is_terminal() or state.is_on_trap(state.hero_pos):
            return state.evaluate(is_expectimax=False)
        v = math.inf
        for action in state.get_legal_actions(1):
            v = min(v, max_value(state.generate_successor(1, action), depth - 1))
        return v

    def max_value(state: GameState, depth: int):
        if depth == 0 or state.is_terminal() or state.is_on_trap(state.hero_pos):
            return state.evaluate(is_expectimax=False)
        v = -math.inf
        for action in state.get_legal_actions(0):
            v = max(v, min_value(state.generate_successor(0, action), depth - 1))
        return v

    best_action, best_score = "STOP", -math.inf
    for action in initial_state.get_legal_actions(0):
        score = min_value(initial_state.generate_successor(0, action), max_depth - 1)
        if score > best_score: best_score, best_action = score, action
    return best_action


def get_best_action_alphabeta(grid, hero_pos, boss_pos, goal_pos, hero_history, known_traps, max_depth=4) -> str:
    # 1. Cập nhật bản đồ: phát hiện bẫy TRONG TRÍ NHỚ và biến nó thành tường
    updated_grid = get_updated_grid(grid, known_traps)
    # 2. Truyền bản đồ MỚI vào BFS để tìm đường đi né bẫy
    dist_map = compute_distance_map(updated_grid, goal_pos)
    # 3. Khởi tạo GameState với bản đồ MỚI
    initial_state = GameState(updated_grid, dist_map, hero_pos, boss_pos, goal_pos, hero_history, known_traps)

    def min_value(state: GameState, depth: int, alpha: float, beta: float):
        if depth == 0 or state.is_terminal() or state.is_on_trap(state.hero_pos):
            return state.evaluate(is_expectimax=False)
        v = math.inf
        for action in state.get_legal_actions(1):
            v = min(v, max_value(state.generate_successor(1, action), depth - 1, alpha, beta))
            if v <= alpha: return v
            beta = min(beta, v)
        return v

    def max_value(state: GameState, depth: int, alpha: float, beta: float):
        if depth == 0 or state.is_terminal() or state.is_on_trap(state.hero_pos):
            return state.evaluate(is_expectimax=False)
        v = -math.inf
        for action in state.get_legal_actions(0):
            v = max(v, min_value(state.generate_successor(0, action), depth - 1, alpha, beta))
            if v >= beta: return v
            alpha = max(alpha, v)
        return v

    best_action, best_score, alpha, beta = "STOP", -math.inf, -math.inf, math.inf
    actions = initial_state.get_legal_actions(0)
    random.shuffle(actions)
    for action in actions:
        score = min_value(initial_state.generate_successor(0, action), max_depth - 1, alpha, beta)
        if score > best_score: best_score, best_action = score, action
        alpha = max(alpha, best_score)
    return best_action


def get_best_action_expectimax(grid, hero_pos, boss_pos, goal_pos, hero_history, known_traps, max_depth=3) -> str:
    # 1. TẠO ẢO GIÁC CHO BFS: Bắt BFS vòng qua bẫy để ưu tiên tìm đường an toàn trước.
    updated_grid = get_updated_grid(grid, known_traps)
    dist_map = compute_distance_map(updated_grid, goal_pos)

    # 2. KHỞI TẠO GAMESTATE THỰC: Vẫn dùng lưới gốc để Hero vẫn CÓ QUYỀN dẫm bẫy nếu bị dồn ép.
    initial_state = GameState(grid, dist_map, hero_pos, boss_pos, goal_pos, hero_history, known_traps)

    # Đổi hàm của Boss thành Min (Boss là kẻ săn mồi tối ưu, không phải đi ngẫu nhiên)
    def min_value(state: GameState, depth: int):
        if depth == 0 or state.is_terminal(): return state.evaluate(is_expectimax=True)
        v = math.inf
        for action in state.get_legal_actions(1):
            v = min(v, max_value(state.generate_successor(1, action), depth - 1))
        return v

    def max_value(state: GameState, depth: int):
        if depth == 0 or state.is_terminal(): return state.evaluate(is_expectimax=True)
        v = -math.inf

        for action in state.get_legal_actions(0, is_expectimax=True):
            next_state = state.generate_successor(0, action)

            if next_state.is_on_trap(next_state.hero_pos):
                # NÚT CƠ HỘI (CHANCE NODE): 10% Chết ngắc (-999999) + 90% Đi tiếp (Trạng thái Min)
                val = (0.10 * -999999) + (0.90 * min_value(next_state, depth - 1))
            else:
                val = min_value(next_state, depth - 1)
            v = max(v, val)
        return v

    best_action, best_score = "STOP", -math.inf

    for action in initial_state.get_legal_actions(0, is_expectimax=True):
        next_state = initial_state.generate_successor(0, action)

        if next_state.is_on_trap(next_state.hero_pos):
            # Tính toán phần trăm thuần túy, không cần gán cứng khoảng cách
            score = (0.10 * -999999) + (0.90 * min_value(next_state, max_depth - 1))
        else:
            score = min_value(next_state, max_depth - 1)

        if score > best_score:
            best_score, best_action = score, action

    return best_action

    def max_value(state: GameState, depth: int):
        if depth == 0 or state.is_terminal(): return state.evaluate(is_expectimax=True)
        v = -math.inf
        # Bật cờ is_expectimax=True để Hero TÍNH CẢ BẪY vào con đường
        for action in state.get_legal_actions(0, is_expectimax=True):
            next_state = state.generate_successor(0, action)
            if next_state.is_on_trap(next_state.hero_pos):
                val = (0.10 * -999999) + (0.90 * exp_value(next_state, depth - 1))
            else:
                val = exp_value(next_state, depth - 1)
            v = max(v, val)
        return v

    best_action, best_score = "STOP", -math.inf
    # Bật cờ is_expectimax=True
    for action in initial_state.get_legal_actions(0, is_expectimax=True):
        next_state = initial_state.generate_successor(0, action)
        if next_state.is_on_trap(next_state.hero_pos):
            score = (0.10 * -999999) + (0.90 * exp_value(next_state, max_depth - 1))
        else:
            score = exp_value(next_state, max_depth - 1)

        if score > best_score: best_score, best_action = score, action

    return best_action