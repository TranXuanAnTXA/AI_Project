"""Uninformed search algorithms (Dành riêng cho nhánh hoang_anh để vẽ UI)."""

from collections import deque
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors, reconstruct_path

def bfs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    Thuật toán Breadth-First Search dạng Generator.
    Mỗi bước duyệt sẽ yield trạng thái để UI vẽ lên màn hình.
    """
    validate_grid(grid)

    queue = deque([start])
    visited = {start}
    came_from = {start: None}

    while queue:
        current = queue.popleft()

        # Nếu tìm thấy đích, yield kết quả cuối cùng kèm đường đi
        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            yield current, visited, list(queue), final_path
            break

        # Duyệt các ô láng giềng xung quanh
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

        # SỬA LỖI 1: Nhả ra mảng rỗng [] thay vì None khi chưa tìm thấy đích
        yield current, visited, list(queue), []

def dfs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    Thuật toán Depth-First Search dạng Generator.
    """
    validate_grid(grid)

    stack = [start]
    visited = {start}
    came_from = {start: None}

    while stack:
        current = stack.pop()

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            yield current, visited, stack, final_path
            break

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                stack.append(neighbor)

        # SỬA LỖI 1: Nhả ra mảng rỗng [] thay vì None khi chưa tìm thấy đích
        yield current, visited, stack, []