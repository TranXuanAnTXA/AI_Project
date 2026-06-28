"""
📄 src/algorithms/dynamic_env.py
* Cập nhật: Fix tương thích hoàn toàn với SimulationManager.
* LRTA* trả về lộ trình tích lũy (actual_path).
* AND-OR trả về kịch bản lý tưởng (happy_path).
"""
import math
import random
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors

def manhattan(a: Coordinate, b: Coordinate) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
def lrta_star_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)
    h_table: dict[Coordinate, float] = {}
    visit_count: dict[Coordinate, int] = {} # [MỚI] Bộ đếm số lần giẫm lên 1 ô

    def get_h(node: Coordinate) -> float:
        if node not in h_table:
            h_table[node] = float(heuristic_fn(node, goal))
        return h_table[node]

    current = start
    visited = {current}
    actual_path = [current]
    metrics = {current: {'h': get_h(current)}}

    while current != goal:
        # Ghi nhận Hero vừa đứng ở ô này thêm 1 lần
        visit_count[current] = visit_count.get(current, 0) + 1

        neighbors = list(iter_neighbors(grid, current))
        if not neighbors:
            yield current, visited, [], None, metrics
            break

        best_neighbors = []
        min_f = math.inf

        for neighbor in neighbors:
            if neighbor == goal:
                cost = 1.0
            else:
                cost = float(grid[neighbor[1]][neighbor[0]]) if grid[neighbor[1]][neighbor[0]] > 0 else 1.0

            # [QUAN TRỌNG] Phạt nặng những ô đã đi qua nhiều lần (chống đi vòng tròn)
            penalty = visit_count.get(neighbor, 0) * 2.0
            f = cost + get_h(neighbor) + penalty

            # Xử lý sai số float và gom các ô có F tốt ngang nhau vào 1 mảng
            if f < min_f - 0.0001:
                min_f = f
                best_neighbors = [neighbor]
            elif abs(f - min_f) <= 0.0001:
                best_neighbors.append(neighbor)

        # [MỚI] Bốc thăm ngẫu nhiên nếu có nhiều ô điểm tốt ngang nhau
        if best_neighbors:
            best_neighbor = random.choice(best_neighbors)
        else:
            break

            # Cập nhật trí nhớ (Học)
        h_table[current] = max(get_h(current), min_f)

        current = best_neighbor
        visited.add(current)
        actual_path.append(current)

        metrics[current] = {'h': get_h(current)}

        yield current, visited, neighbors, None, metrics

    yield current, visited, [], actual_path, metrics


# ==========================================
# 2. AND-OR GRAPH SEARCH
# ==========================================
def and_or_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    validate_grid(grid)
    visited_nodes = {start}

    def get_outcomes(state: Coordinate, action_target: Coordinate):
        """Giả lập môi trường rủi ro: Nếu ô kế là băng (3), có khả năng bị trượt ra xung quanh"""
        outcomes = [action_target]
        cell_val = grid[action_target[1]][action_target[0]]
        if cell_val == 3:
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = action_target[0] + dx, action_target[1] + dy
                if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] != 1:
                    outcomes.append((nx, ny))
        return outcomes

    def or_search(state: Coordinate, path: list):
        visited_nodes.add(state)

        # Nhả yield tĩnh để UI không bị đứng
        yield state, visited_nodes, [state], None, {}

        if state == goal:
            return [state]
        if state in path:
            return None

        for action_target in iter_neighbors(grid, state):
            outcomes = get_outcomes(state, action_target)
            plan = yield from and_search(outcomes, path + [state])

            if plan is not None:
                # Tìm được Happy Path -> Trả về mảng đường đi
                return [state] + plan[action_target]
        return None

    def and_search(states: list, path: list):
        conditional_plans = {}
        for state in states:
            plan = yield from or_search(state, path)
            if plan is None:
                return None # Rủi ro dẫn đến ngõ cụt -> Phá sản nhánh này
            conditional_plans[state] = plan
        return conditional_plans

    # [MỚI]: Nhả frame giả đầu tiên để tránh lỗi "Vét cạn bản đồ"
    yield start, visited_nodes, [start], None, {}

    happy_path = yield from or_search(start, [])

    # Kết thúc: Nhả ra con đường an toàn nhất
    yield start, visited_nodes, [], happy_path, {}