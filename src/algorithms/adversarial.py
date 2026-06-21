"""Adversarial search algorithms (Dành riêng cho nhánh hoang_anh để vẽ UI)."""

import math
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors, reconstruct_path

def evaluate_state(current: Coordinate, goal: Coordinate) -> float:
    """Hàm đánh giá điểm số của ô hiện tại (càng gần đích điểm càng cao)."""
    return - (abs(current[0] - goal[0]) + abs(current[1] - goal[1]))

# ==========================================
# 1. MINIMAX SEARCH
# ==========================================
def minimax_generator(grid: Grid, start: Coordinate, goal: Coordinate, max_depth: int = 3):
    """
    Giả lập thuật toán Minimax trên lưới đồ thị.
    Sử dụng đệ quy (yield from) để giao diện có thể vẽ quá trình đánh giá luân phiên.
    """
    validate_grid(grid)
    visited = set()

    def min_value(current: Coordinate, depth: int):
        visited.add(current)
        yield current, visited.copy(), [], None

        if depth == 0 or current == goal:
            return evaluate_state(current, goal)

        v = math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                val = yield from max_value(neighbor, depth - 1)
                v = min(v, val)
                visited.remove(neighbor) # Backtrack (hồi lại) để thử nhánh khác
        return v

    def max_value(current: Coordinate, depth: int):
        visited.add(current)
        yield current, visited.copy(), [], None

        if depth == 0 or current == goal:
            return evaluate_state(current, goal)

        v = -math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                val = yield from min_value(neighbor, depth - 1)
                v = max(v, val)
                visited.remove(neighbor) # Backtrack
        return v

    # Chạy mô phỏng bắt đầu từ lượt của người chơi Max
    visited.clear()
    yield from max_value(start, max_depth)

    # Kết thúc mô phỏng (Không có đường đi cụ thể vì đây là hàm đánh giá trạng thái)
    yield start, visited, [], [start]


# ==========================================
# 2. ALPHA-BETA PRUNING
# ==========================================
def alpha_beta_generator(grid: Grid, start: Coordinate, goal: Coordinate, max_depth: int = 4):
    """
    Giả lập thuật toán Alpha-Beta Pruning (Minimax có cắt tỉa nhánh).
    """
    validate_grid(grid)
    visited = set()

    def min_value(current: Coordinate, depth: int, alpha: float, beta: float):
        visited.add(current)
        yield current, visited.copy(), [], None

        if depth == 0 or current == goal:
            return evaluate_state(current, goal)

        v = math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                val = yield from max_value(neighbor, depth - 1, alpha, beta)
                v = min(v, val)
                if v <= alpha:
                    visited.remove(neighbor)
                    return v # Cắt tỉa (Pruning) nhánh này
                beta = min(beta, v)
                visited.remove(neighbor)
        return v

    def max_value(current: Coordinate, depth: int, alpha: float, beta: float):
        visited.add(current)
        yield current, visited.copy(), [], None

        if depth == 0 or current == goal:
            return evaluate_state(current, goal)

        v = -math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                val = yield from min_value(neighbor, depth - 1, alpha, beta)
                v = max(v, val)
                if v >= beta:
                    visited.remove(neighbor)
                    return v # Cắt tỉa (Pruning) nhánh này
                alpha = max(alpha, v)
                visited.remove(neighbor)
        return v

    visited.clear()
    # Chạy mô phỏng bắt đầu từ lượt Max với Alpha = -Vô cực, Beta = +Vô cực
    yield from max_value(start, max_depth, -math.inf, math.inf)

    # Nhả frame cuối cùng
    yield start, visited, [], [start]