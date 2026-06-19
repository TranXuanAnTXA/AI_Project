"""
* Vai trò cốt lõi (Purpose): Triển khai các thuật toán tìm đường (Pathfinding) cụ thể trên không gian lưới 2D.
* Cách hoạt động (How it works): Mỗi thuật toán nhận đầu vào là ma trận, điểm bắt đầu, điểm đích. Chúng sử dụng các cấu trúc dữ liệu đặc thù (Hàng đợi/Queue cho BFS, Ngăn xếp/Stack cho DFS, Hàng đợi ưu tiên/Heap cho A* và Greedy) để duyệt qua các ô, ghi nhận lịch sử và trả về kết quả chuẩn hóa (PathSearchResult).
* Các Hàm chính (Core Functions):
    - bfs(): Tìm kiếm theo chiều rộng, đảm bảo đường đi ngắn nhất (chậm, tốn RAM).
    - dfs(): Tìm kiếm theo chiều sâu, đi tới cùng một nhánh (nhanh nhưng không tối ưu).
    - a_star(): Tìm kiếm thông minh, kết hợp chi phí thực tế và heuristic (tối ưu, cân bằng).
    - greedy(): Tìm kiếm tham lam, luôn hướng về đích (nhanh nhưng dễ kẹt).
* Mối liên hệ (Dependencies): Gọi các hàm hỗ trợ và kiểu dữ liệu từ `common.py`. Phụ thuộc vào `heuristics.py` để tính khoảng cách (dành cho A* và Greedy).
"""

from __future__ import annotations

from collections import deque
from heapq import heappop, heappush
from itertools import count
from math import inf

from .common import Coordinate, Grid, PathSearchResult, iter_neighbors, reconstruct_path, validate_grid
from src.algorithms.utils.heuristics import manhattan


def bfs(grid: Grid, start: Coordinate, goal: Coordinate) -> PathSearchResult:
    validate_grid(grid)
    queue = deque([start])
    came_from: dict[Coordinate, Coordinate | None] = {start: None}
    visited_order: list[Coordinate] = []
    expanded_nodes = 0
    frontier_max_size = 1

    while queue:
        frontier_max_size = max(frontier_max_size, len(queue))
        current = queue.popleft()
        expanded_nodes += 1
        visited_order.append(current)

        if current == goal:
            return PathSearchResult(
                path=reconstruct_path(came_from, goal),
                visited_order=visited_order,
                expanded_nodes=expanded_nodes,
                frontier_max_size=frontier_max_size,
                found=True,
            )

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    return PathSearchResult(path=[], visited_order=visited_order, expanded_nodes=expanded_nodes, frontier_max_size=frontier_max_size, found=False)


def dfs(grid: Grid, start: Coordinate, goal: Coordinate) -> PathSearchResult:
    validate_grid(grid)
    stack = [start]
    came_from: dict[Coordinate, Coordinate | None] = {start: None}
    visited_order: list[Coordinate] = []
    visited: set[Coordinate] = set()
    expanded_nodes = 0
    frontier_max_size = 1

    while stack:
        frontier_max_size = max(frontier_max_size, len(stack))
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        expanded_nodes += 1
        visited_order.append(current)

        if current == goal:
            return PathSearchResult(
                path=reconstruct_path(came_from, goal),
                visited_order=visited_order,
                expanded_nodes=expanded_nodes,
                frontier_max_size=frontier_max_size,
                found=True,
            )

        neighbors = list(iter_neighbors(grid, current))
        for neighbor in reversed(neighbors):
            if neighbor not in came_from:
                came_from[neighbor] = current
                stack.append(neighbor)

    return PathSearchResult(path=[], visited_order=visited_order, expanded_nodes=expanded_nodes, frontier_max_size=frontier_max_size, found=False)


def a_star(grid: Grid, start: Coordinate, goal: Coordinate) -> PathSearchResult:
    validate_grid(grid)
    open_heap: list[tuple[int, int, Coordinate]] = []
    order = count()
    heappush(open_heap, (manhattan(start, goal), next(order), start))
    came_from: dict[Coordinate, Coordinate | None] = {start: None}
    g_score: dict[Coordinate, int] = {start: 0}
    closed: set[Coordinate] = set()
    visited_order: list[Coordinate] = []
    expanded_nodes = 0
    frontier_max_size = 1

    while open_heap:
        frontier_max_size = max(frontier_max_size, len(open_heap))
        _, _, current = heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        expanded_nodes += 1
        visited_order.append(current)

        if current == goal:
            return PathSearchResult(
                path=reconstruct_path(came_from, goal),
                visited_order=visited_order,
                expanded_nodes=expanded_nodes,
                frontier_max_size=frontier_max_size,
                found=True,
            )

        current_cost = g_score[current]
        for neighbor in iter_neighbors(grid, current):
            tentative_cost = current_cost + 1
            if tentative_cost < g_score.get(neighbor, inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_cost
                priority = tentative_cost + manhattan(neighbor, goal)
                heappush(open_heap, (priority, next(order), neighbor))

    return PathSearchResult(path=[], visited_order=visited_order, expanded_nodes=expanded_nodes, frontier_max_size=frontier_max_size, found=False)


def greedy(grid: Grid, start: Coordinate, goal: Coordinate) -> PathSearchResult:
    validate_grid(grid)
    open_heap: list[tuple[int, int, Coordinate]] = []
    order = count()
    heappush(open_heap, (manhattan(start, goal), next(order), start))
    came_from: dict[Coordinate, Coordinate | None] = {start: None}
    visited: set[Coordinate] = set()
    visited_order: list[Coordinate] = []
    expanded_nodes = 0
    frontier_max_size = 1

    while open_heap:
        frontier_max_size = max(frontier_max_size, len(open_heap))
        _, _, current = heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)
        expanded_nodes += 1
        visited_order.append(current)

        if current == goal:
            return PathSearchResult(
                path=reconstruct_path(came_from, goal),
                visited_order=visited_order,
                expanded_nodes=expanded_nodes,
                frontier_max_size=frontier_max_size,
                found=True,
            )

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                heappush(open_heap, (manhattan(neighbor, goal), next(order), neighbor))

    return PathSearchResult(path=[], visited_order=visited_order, expanded_nodes=expanded_nodes, frontier_max_size=frontier_max_size, found=False)
