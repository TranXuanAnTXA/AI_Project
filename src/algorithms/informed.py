"""Informed search algorithms (Dành riêng cho nhánh hoang_anh để vẽ UI)."""

import heapq
import math
from collections import deque
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors, reconstruct_path

def manhattan(a: Coordinate, b: Coordinate) -> float:
    """Hàm tính khoảng cách heuristic (Manhattan) cơ bản."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# ==========================================
# 1. GREEDY BEST-FIRST SEARCH
# ==========================================
def greedy_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)

    h_start = heuristic_fn(start, goal)
    open_set = []
    heapq.heappush(open_set, (h_start, start))

    came_from = {start: None}
    visited = set()

    # Lưu trữ điểm số để hiển thị lên Bảng thanh tra (Inspector Panel)
    metrics = {start: {'h': h_start, 'f': h_start, 'cost': 0}}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            frontier = [item[1] for item in open_set]
            yield current, visited, frontier, final_path, metrics
            break

        visited.add(current)

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited and neighbor not in [item[1] for item in open_set]:
                came_from[neighbor] = current
                h_val = heuristic_fn(neighbor, goal)
                heapq.heappush(open_set, (h_val, neighbor))

                # Ghi nhận thông số (Greedy chỉ quan tâm hàm H)
                cell_val = grid[neighbor[0]][neighbor[1]]
                step_cost = float(cell_val) if cell_val > 0 else 1.0
                metrics[neighbor] = {'h': h_val, 'f': h_val, 'cost': step_cost}

        frontier = [item[1] for item in open_set]
        yield current, visited, frontier, None, metrics

# ==========================================
# 2. A* SEARCH
# ==========================================
def astar_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)

    open_set = []
    heapq.heappush(open_set, (0.0, start))

    came_from = {start: None}
    g_score = {start: 0.0}
    visited = set()

    # Khởi tạo metrics với đầy đủ G, H, F
    h_start = heuristic_fn(start, goal)
    metrics = {start: {'g': 0.0, 'h': h_start, 'f': h_start, 'cost': 0}}

    # [CÂN BẰNG GAME]: Hệ số Weighted A*.
    # > 1.0: Ưu tiên đâm thẳng về đích (Dễ dẫm bẫy bùn, tốn Thể lực).
    # = 1.0: A* Chuẩn (An toàn, tốn ít Thể lực nhưng quét nhiều CPU).
    epsilon = 1.0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            frontier = [item[1] for item in open_set]
            yield current, visited, frontier, final_path, metrics
            break

        visited.add(current)

        for neighbor in iter_neighbors(grid, current):
            # Tính Cost từ ma trận (Bùn = 5, Sàn = 1)
            cell_val = grid[neighbor[0]][neighbor[1]]
            step_cost = float(cell_val) if cell_val > 0 else 1.0

            tentative_g = g_score[current] + step_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h_val = heuristic_fn(neighbor, goal)

                # Tính tổng điểm ưu tiên F có áp dụng hệ số (Weighted A*)
                f_score = tentative_g + (epsilon * h_val)

                heapq.heappush(open_set, (f_score, neighbor))
                metrics[neighbor] = {'g': tentative_g, 'h': h_val, 'f': f_score, 'cost': step_cost}

        frontier = [item[1] for item in open_set]
        yield current, visited, frontier, None, metrics

# ==========================================
# 3. BIDIRECTIONAL SEARCH
# ==========================================
def bidirectional_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    validate_grid(grid)

    forward_queue = deque([start])
    backward_queue = deque([goal])

    forward_came_from = {start: None}
    backward_came_from = {goal: None}

    forward_visited = {start}
    backward_visited = {goal}

    # Bidirectional lan tỏa mù, không có Heuristic để thanh tra
    metrics = {}

    while forward_queue and backward_queue:
        # --- Lan tỏa từ Start ---
        current_f = forward_queue.popleft()
        if current_f in backward_visited:
            path_f = reconstruct_path(forward_came_from, current_f)
            curr = backward_came_from[current_f]
            path_b = []
            while curr is not None:
                path_b.append(curr)
                curr = backward_came_from[curr]
            final_path = path_f + path_b
            yield current_f, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), final_path, metrics
            break

        for neighbor in iter_neighbors(grid, current_f):
            if neighbor not in forward_visited:
                forward_visited.add(neighbor)
                forward_came_from[neighbor] = current_f
                forward_queue.append(neighbor)

        yield current_f, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), None, metrics

        # --- Lan tỏa từ Goal ---
        current_b = backward_queue.popleft()
        if current_b in forward_visited:
            path_f = reconstruct_path(forward_came_from, current_b)
            curr = backward_came_from[current_b]
            path_b = []
            while curr is not None:
                path_b.append(curr)
                curr = backward_came_from[curr]
            final_path = path_f + path_b
            yield current_b, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), final_path, metrics
            break

        for neighbor in iter_neighbors(grid, current_b):
            if neighbor not in backward_visited:
                backward_visited.add(neighbor)
                backward_came_from[neighbor] = current_b
                backward_queue.append(neighbor)

        yield current_b, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), None, metrics

# ==========================================
# 4. IDA* SEARCH
# ==========================================
def idastar_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)
    threshold = heuristic_fn(start, goal)
    came_from = {start: None}
    visited = set()
    metrics = {}

    def search(current, g_score, current_threshold):
        h_val = heuristic_fn(current, goal)
        f_score = g_score + h_val
        visited.add(current)

        # Ghi nhận trạng thái để thanh tra đệ quy
        cell_val = grid[current[0]][current[1]]
        step_cost = float(cell_val) if cell_val > 0 else 1.0
        metrics[current] = {'g': g_score, 'h': h_val, 'f': f_score, 'cost': step_cost}

        yield current, visited.copy(), [], None, metrics

        if f_score > current_threshold:
            return f_score
        if current == goal:
            return "FOUND"

        min_exceeded = math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                came_from[neighbor] = current

                cell_val = grid[neighbor[0]][neighbor[1]]
                step_cost = float(cell_val) if cell_val > 0 else 1.0

                result = yield from search(neighbor, g_score + step_cost, current_threshold)
                if result == "FOUND":
                    return "FOUND"
                if result < min_exceeded:
                    min_exceeded = result
                visited.remove(neighbor)
        return min_exceeded

    while True:
        visited.clear()
        result = yield from search(start, 0.0, threshold)

        if result == "FOUND":
            final_path = reconstruct_path(came_from, goal)
            yield goal, visited, [], final_path, metrics
            break
        if result == math.inf:
            yield start, visited, [], [], metrics
            break
        threshold = result