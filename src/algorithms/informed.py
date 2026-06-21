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

    # Priority Queue lưu (h_score, tọa độ)
    open_set = []
    heapq.heappush(open_set, (heuristic_fn(start, goal), start))

    came_from = {start: None}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            frontier = [item[1] for item in open_set]
            yield current, visited, frontier, final_path
            break

        visited.add(current)

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited and neighbor not in [item[1] for item in open_set]:
                came_from[neighbor] = current
                heapq.heappush(open_set, (heuristic_fn(neighbor, goal), neighbor))

        frontier = [item[1] for item in open_set]
        yield current, visited, frontier, None

# ==========================================
# 2. A* SEARCH
# ==========================================
def astar_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)

    # Priority Queue lưu (f_score, tọa độ)
    open_set = []
    heapq.heappush(open_set, (0.0, start))

    came_from = {start: None}
    g_score = {start: 0.0}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            frontier = [item[1] for item in open_set]
            yield current, visited, frontier, final_path
            break

        visited.add(current)

        for neighbor in iter_neighbors(grid, current):
            tentative_g = g_score[current] + 1.0 # Chi phí đi 1 bước luôn là 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic_fn(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

        frontier = [item[1] for item in open_set]
        yield current, visited, frontier, None

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

    while forward_queue and backward_queue:
        # --- Lan tỏa từ Start ---
        current_f = forward_queue.popleft()
        if current_f in backward_visited:
            path_f = reconstruct_path(forward_came_from, current_f)
            # Nối đường đi từ nhánh backward ngược lại
            curr = backward_came_from[current_f]
            path_b = []
            while curr is not None:
                path_b.append(curr)
                curr = backward_came_from[curr]
            final_path = path_f + path_b
            yield current_f, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), final_path
            break

        for neighbor in iter_neighbors(grid, current_f):
            if neighbor not in forward_visited:
                forward_visited.add(neighbor)
                forward_came_from[neighbor] = current_f
                forward_queue.append(neighbor)

        yield current_f, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), None

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
            yield current_b, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), final_path
            break

        for neighbor in iter_neighbors(grid, current_b):
            if neighbor not in backward_visited:
                backward_visited.add(neighbor)
                backward_came_from[neighbor] = current_b
                backward_queue.append(neighbor)

        yield current_b, forward_visited | backward_visited, list(forward_queue) + list(backward_queue), None

# ==========================================
# 4. IDA* SEARCH
# ==========================================
def idastar_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    """Sử dụng yield from để đệ quy Generator vẽ được ra UI."""
    validate_grid(grid)
    threshold = heuristic_fn(start, goal)
    came_from = {start: None}
    visited = set()

    def search(current, g_score, current_threshold):
        f_score = g_score + heuristic_fn(current, goal)
        visited.add(current)

        # Nhả trạng thái hiện tại ra UI (Frontier rỗng do IDA* dùng đệ quy sâu)
        yield current, visited.copy(), [], None

        if f_score > current_threshold:
            return f_score
        if current == goal:
            return "FOUND"

        min_exceeded = math.inf
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                came_from[neighbor] = current
                # Đệ quy gọi hàm yield từ bên trong
                result = yield from search(neighbor, g_score + 1.0, current_threshold)
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
            yield goal, visited, [], final_path
            break
        if result == math.inf:
            yield start, visited, [], [] # Không tìm thấy
            break
        threshold = result